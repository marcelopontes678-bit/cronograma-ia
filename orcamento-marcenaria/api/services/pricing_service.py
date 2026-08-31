"""Ponte fina entre a API (ExtracaoResultado, schema Vision) e o motor de
precificacao existente (engine/calculo_projeto.py + engine/orcamento_engine.py,
ja testados com o projeto real Quarto Maria). Nao reimplementa a formula
de markup nem a logica de chapa/fita/ferragem -- so adapta o formato.

Limitacao honesta e deliberada: a extracao via Vision da so a dimensao
FRONTAL de cada modulo (largura x altura), nao a lista de pecas cortadas
(fundo, laterais, prateleiras) que o Promob fornece. Area frontal NAO e
area real de chapa -- por isso um modulo so entra no calculo de chapa/fita
quando o chamador informa `fator_area_frontal_para_chapa` (multiplicador
frontal->real, o mesmo numero que o usuario nao quis fornecer no episodio
manual desta conversa). Sem esse fator, o modulo fica pendente e listado
em avisos, nunca com area estimada silenciosamente.

Contagem de ferragens (dobradicas, corredicas) a partir de
quantidade_portas/quantidade_gavetas NAO e feita nesta versao -- exigiria
regras de negocio (quantas dobradicas por porta, etc) que ainda nao
existem em PreferenciasGlobais. Fica como aviso explicito, nao como
custo zero silencioso.
"""
from __future__ import annotations

import sys
from pathlib import Path

from api.schemas.extracao import ExtracaoResultado, Modulo
from api.schemas.orcamento import ItemPendente, OrcamentoResponse

_DIR_ENGINE = Path(__file__).resolve().parent.parent.parent / "engine"
if str(_DIR_ENGINE) not in sys.path:
    sys.path.insert(0, str(_DIR_ENGINE))

from calculo_projeto import calcular_projeto  # noqa: E402
from orcamento_engine import calcular_orcamento_projeto, carregar_config  # noqa: E402
from tabela_precos import carregar_tabela_precos  # noqa: E402


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
    resultado: ExtracaoResultado,
    fator_area_frontal_para_chapa: float | None,
    avisos: list[str],
) -> list[dict]:
    ambientes_json = []
    for ambiente in resultado.ambientes:
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
                    f"(ferragens_sugeridas pelo MAX: {[f.nome for f in modulo.ferragens_sugeridas]})."
                )

        if itens:
            ambientes_json.append(
                {"nome": ambiente.nome_ambiente, "modulos": [{"nome": ambiente.nome_ambiente, "itens": itens}]}
            )

    return ambientes_json


def gerar_orcamento(
    resultado: ExtracaoResultado,
    caminho_tabela_precos: str | Path,
    caminho_config_precificacao: str | Path,
    faturamento_acumulado: float,
    custo_hora_mao_de_obra: float = 0.0,
    horas_estimadas: float = 0.0,
    fator_area_frontal_para_chapa: float | None = None,
) -> tuple[OrcamentoResponse, list[str]]:
    """Retorna (OrcamentoResponse, avisos). `resultado` precisa estar
    CONFIRMADO -- a rota da API e responsavel por checar isso antes de
    chamar (ver POST /orcamentos em api/ROTAS.md)."""
    from api.schemas.extracao import StatusExtracao

    if resultado.status != StatusExtracao.CONFIRMADO:
        raise PrecificacaoInvalidaError(
            f"job={resultado.job_id}: status e {resultado.status!r}, precisa estar CONFIRMADO antes de precificar."
        )

    avisos: list[str] = []
    ambientes_json = _construir_ambientes_json(resultado, fator_area_frontal_para_chapa, avisos)

    tabela = carregar_tabela_precos(caminho_tabela_precos)
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
        job_id=resultado.job_id,
        divisor_markup=resultado_orcamento.divisor_markup,
        custo_material_total=resultado_orcamento.custo_material_total,
        preco_venda_material=resultado_orcamento.preco_venda_material,
        custo_mao_de_obra=resultado_orcamento.custo_mao_de_obra,
        total=resultado_orcamento.total,
        itens_pendentes=itens_pendentes,
    )
    return response, avisos
