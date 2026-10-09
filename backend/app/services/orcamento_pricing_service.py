"""Ponte fina entre o dominio de orcamento (OrcamentoJob, schema Vision) e o
motor de precificacao existente (app/engine/calculo_projeto.py +
app/engine/orcamento_engine.py, ja testados com o projeto real Quarto
Maria). Nao reimplementa a formula de markup nem a logica de chapa/fita/
ferragem -- so adapta o formato.

Limitacao honesta e deliberada: a extracao via Vision da so a dimensao
FRONTAL de cada modulo (largura x altura), nao a lista de pecas cortadas
(fundo, laterais, prateleiras) que o Promob fornece. Area frontal NAO e
area real de chapa -- por isso um modulo so entra no calculo de chapa/fita
quando o chamador informa `fator_area_frontal_para_chapa` (multiplicador
frontal->real). Sem esse fator, o modulo fica pendente e listado em
avisos, nunca com area estimada silenciosamente.

Material em texto livre (o que o MARC le do PDF, ex: "MDF Branco") e
casado com uma chapa da tabela de precos via orcamento_material_matcher
antes do calculo -- so casamentos confiantes trocam o `reference` do item;
os demais ficam pendentes e todo casamento aplicado aparece em avisos.

Contagem de ferragens (dobradicas, corredicas) a partir de
quantidade_portas/quantidade_gavetas NAO e feita nesta versao -- fica como
aviso explicito, nao como custo zero silencioso.
"""
from __future__ import annotations

from pathlib import Path

from app.engine.calculo_projeto import calcular_projeto
from app.engine.orcamento_engine import calcular_orcamento_projeto, carregar_config
from app.engine.tabela_precos import PrecoReferencia, carregar_tabela_precos
from app.models.orcamento import OrcamentoJob, StatusOrcamentoJob
from app.schemas.orcamento import Ambiente, ItemPendente, Modulo, OrcamentoResponse
from app.services import orcamento_material_matcher
from app.services.orcamento_material_matcher import CasamentoMaterialError


class PrecificacaoInvalidaError(Exception):
    pass


def _modulo_para_item_promob(modulo: Modulo) -> dict | None:
    """Converte um Modulo (schema Vision) num item no formato que
    calculo_projeto.py espera (mesmo shape dos itens do extractor Promob).
    Retorna None quando o modulo nao tem dimensoes suficientes para virar
    um item de chapa (nunca inventa largura/altura ausente)."""
    largura_mm = modulo.dimensoes.largura_mm
    altura_mm = modulo.dimensoes.altura_mm
    if largura_mm is None or altura_mm is None:
        return None

    return {
        "unidade": "M2",
        # caixaria e o material que domina a area de chapa (frente/fundo sao acabamentos de superficie menor)
        "reference": modulo.especificacoes_materiais.caixaria,
        "quantidade": (largura_mm / 1000.0) * (altura_mm / 1000.0),  # area FRONTAL em m2, nao area de chapa
        "repeticao": 1,
        "largura_mm": largura_mm,
        "altura_mm": altura_mm,
        "profundidade_mm": modulo.dimensoes.profundidade_mm,
        "descricao": modulo.nome,
        "origem": f"modulo_id={modulo.id}",
    }


def _construir_ambientes_json(
    ambientes: list[Ambiente],
    fator_area_frontal_para_chapa: float | None,
    avisos: list[str],
) -> list[dict]:
    ambientes_json = []
    for ambiente in ambientes:
        itens = []
        for modulo in ambiente.modulos:
            if fator_area_frontal_para_chapa is None:
                avisos.append(
                    f"{modulo.id} ({modulo.nome}): fator_area_frontal_para_chapa nao informado -- "
                    f"modulo NAO incluido no calculo de chapa/fita (so area frontal foi extraida, nao area real de corte)."
                )
                continue

            item = _modulo_para_item_promob(modulo)
            if item is None:
                avisos.append(f"{modulo.id} ({modulo.nome}): sem largura/altura extraidas -- nao incluido no calculo.")
                continue

            item["quantidade"] *= fator_area_frontal_para_chapa
            itens.append(item)

            portas = modulo.componentes.portas
            gavetas = modulo.componentes.gavetas
            if portas or gavetas:
                avisos.append(
                    f"{modulo.id} ({modulo.nome}): {portas} porta(s) / "
                    f"{gavetas} gaveta(s) detectadas, mas contagem de ferragens "
                    f"(dobradicas/corredicas) ainda nao e calculada automaticamente nesta versao "
                    f"(ferragens_sugeridas pelo MARC: {[f.nome for f in modulo.ferragens_sugeridas]})."
                )

        if itens:
            ambientes_json.append(
                {"nome": ambiente.nome_ambiente, "modulos": [{"nome": ambiente.nome_ambiente, "itens": itens}]}
            )

    return ambientes_json


def _casar_materiais_texto_livre(
    ambientes_json: list[dict],
    tabela: dict[str, PrecoReferencia],
    espessura_padrao_caixa_mm: float | None,
    api_key: str,
    modelo: str,
    avisos: list[str],
) -> None:
    """Troca, in place, o `reference` em texto livre dos itens M2 pelo
    REFERENCE da chapa casada na tabela. Falha de API ou falta de chave
    nao derrubam o orcamento: os itens ficam pendentes (sem preco, nunca
    estimado) e o motivo vai para avisos."""
    itens = [
        it
        for amb in ambientes_json
        for mod in amb["modulos"]
        for it in mod["itens"]
        if it.get("unidade") == "M2" and orcamento_material_matcher.precisa_casar(it.get("reference"), tabela)
    ]
    if not itens:
        return

    materiais = list(dict.fromkeys(it["reference"] for it in itens))
    if not api_key:
        avisos.append(
            f"ANTHROPIC_API_KEY nao configurada -- material(is) {materiais} nao foram casados com a "
            f"tabela de precos e ficaram pendentes."
        )
        return

    try:
        casamentos = orcamento_material_matcher.casar_materiais(
            materiais,
            orcamento_material_matcher.chapas_candidatas(tabela),
            espessura_padrao_caixa_mm,
            api_key,
            modelo,
        )
    except Exception as exc:  # falha de rede/API -- itens ficam pendentes, motivo visivel
        if not isinstance(exc, CasamentoMaterialError):
            exc = CasamentoMaterialError(f"falha ao chamar a API: {exc}")
        avisos.append(f"Casamento de materiais com a tabela de precos falhou ({exc}) -- {materiais} ficaram pendentes.")
        return

    for material in materiais:
        casamento = casamentos[material]
        if casamento.aplicavel:
            avisos.append(
                f"Material '{material}' casado com a chapa '{casamento.chapa.reference}' "
                f"({casamento.chapa.descricao}), confianca {casamento.confianca:.2f} -- confira antes de enviar ao cliente."
            )
        elif casamento.chapa is not None:
            avisos.append(
                f"Material '{material}': possivel chapa '{casamento.chapa.reference}' ({casamento.chapa.descricao}), "
                f"mas com confianca baixa ({casamento.confianca:.2f}) -- ficou pendente, confirme o material."
            )
        else:
            avisos.append(f"Material '{material}': nenhuma chapa correspondente na tabela de precos -- ficou pendente.")

    for item in itens:
        casamento = casamentos[item["reference"]]
        if casamento.aplicavel:
            item["reference"] = casamento.chapa.reference


def gerar_orcamento(
    job: OrcamentoJob,
    caminho_tabela_precos: str | Path,
    caminho_config_precificacao: str | Path,
    faturamento_acumulado: float,
    custo_hora_mao_de_obra: float = 0.0,
    horas_estimadas: float = 0.0,
    fator_area_frontal_para_chapa: float | None = None,
    espessura_padrao_caixa_mm: float | None = None,
    api_key: str = "",
    modelo: str = orcamento_material_matcher.MODELO_PADRAO,
) -> tuple[OrcamentoResponse, list[str]]:
    """Retorna (OrcamentoResponse, avisos). `job` precisa estar
    CONFIRMADO -- o router e responsavel por checar isso antes de chamar.
    Sincrono/bloqueante (pode chamar a API do Claude) -- rode via
    asyncio.to_thread a partir de rota async."""
    if job.status != StatusOrcamentoJob.CONFIRMADO:
        raise PrecificacaoInvalidaError(
            f"job={job.id}: status e {job.status!r}, precisa estar CONFIRMADO antes de precificar."
        )

    ambientes = [Ambiente.model_validate(a) for a in job.ambientes]

    avisos: list[str] = []
    ambientes_json = _construir_ambientes_json(ambientes, fator_area_frontal_para_chapa, avisos)

    tabela = carregar_tabela_precos(caminho_tabela_precos)
    _casar_materiais_texto_livre(ambientes_json, tabela, espessura_padrao_caixa_mm, api_key, modelo, avisos)
    resultado_calculo = calcular_projeto(ambientes_json, tabela) if ambientes_json else None

    custo_material_total = resultado_calculo.custo_material_total if resultado_calculo else 0.0

    config = carregar_config(caminho_config_precificacao)
    resultado_orcamento = calcular_orcamento_projeto(
        custo_material_total,
        config,
        faturamento_acumulado,
        custo_mao_de_obra=custo_hora_mao_de_obra * horas_estimadas,
    )

    itens_pendentes = []
    if resultado_calculo:
        for ref, desc, motivo in resultado_calculo.itens_sem_preco:
            itens_pendentes.append(ItemPendente(reference_ou_acabamento=ref, descricao=desc, motivo=motivo))

    response = OrcamentoResponse(
        job_id=job.id,
        divisor_markup=resultado_orcamento.divisor_markup,
        custo_material_total=resultado_orcamento.custo_material_total,
        preco_venda_material=resultado_orcamento.preco_venda_material,
        custo_mao_de_obra=resultado_orcamento.custo_mao_de_obra,
        total=resultado_orcamento.total,
        itens_pendentes=itens_pendentes,
        avisos=avisos,
    )
    return response, avisos
