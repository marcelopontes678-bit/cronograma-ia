"""Calcula o custo de material do projeto inteiro por CHAPA FECHADA + FITA DE
BORDA (itens de unidade M2, tipicamente pecas de MDF) + FERRAGENS (itens de
unidade UN), em vez de precificar peca por peca.

Logica:
- Chapas: soma a area (m2) de todas as pecas M2 do mesmo REFERENCE, aplica
  uma % de perda de corte, divide pela area util de uma chapa padrao e
  arredonda pra cima -> numero de chapas inteiras x preco da chapa.
- Fita de borda: para cada peca M2, estima o perimetro fitavel pelas duas
  maiores dimensoes (largura/altura/profundidade) -- a menor e considerada a
  espessura da chapa e nao entra no perimetro. Soma os metros por REFERENCE
  x preco da fita daquele acabamento.
- Ferragens: preco unitario x quantidade/repeticao, como antes
  (tabela_precos.calcular_custo_item_ferragem).

Nao inventa preco: referencia sem preco cadastrado fica sinalizada como
pendente e NAO entra no total.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from tabela_precos import (
    PrecoReferencia,
    calcular_custo_item_ferragem,
    chave_acabamento,
    indexar_precos_por_acabamento,
)

AREA_UTIL_CHAPA_M2_PADRAO = 2.750 * 1.830  # 5.0325 m2 (chapa 2750x1830mm)
PCT_PERDA_CORTE_PADRAO = 0.15


@dataclass
class ResultadoChapasReferencia:
    acabamento: str  # ex: "18mm Duratex.Essencial.Rosa Infinito"
    area_total_m2: float
    area_com_perda_m2: float
    num_chapas: int
    preco_chapa: float
    custo_chapas: float


@dataclass
class ResultadoFitaReferencia:
    acabamento: str
    metros_total: float
    preco_fita_metro: float
    custo_fita: float


@dataclass
class ResultadoFerragem:
    descricao: str
    reference: str
    preco_unitario: float
    quantidade: int
    custo: float
    origem: str


@dataclass
class ResultadoCalculoProjeto:
    chapas: list[ResultadoChapasReferencia] = field(default_factory=list)
    fitas: list[ResultadoFitaReferencia] = field(default_factory=list)
    ferragens: list[ResultadoFerragem] = field(default_factory=list)
    itens_sem_preco: list[tuple[str, str, str]] = field(default_factory=list)  # (reference, descricao, motivo)

    @property
    def custo_material_total(self) -> float:
        return (
            sum(c.custo_chapas for c in self.chapas)
            + sum(f.custo_fita for f in self.fitas)
            + sum(fe.custo for fe in self.ferragens)
        )


def _perimetro_fitavel_m(largura_mm: float, altura_mm: float, profundidade_mm: float) -> float:
    """As duas maiores dimensoes formam a face visivel da peca; a menor e a
    espessura da chapa e nao entra no perimetro fitavel."""
    dims = sorted([largura_mm or 0, altura_mm or 0, profundidade_mm or 0])
    maior, segunda_maior = dims[-1], dims[-2]
    perimetro_mm = 2 * (maior + segunda_maior)
    return perimetro_mm / 1000.0


def _itens_flat(ambientes_json: list[dict]) -> list[dict]:
    itens = []
    for amb in ambientes_json:
        for mod in amb["modulos"]:
            for it in mod["itens"]:
                itens.append(it)
    return itens


def calcular_projeto(
    ambientes_json: list[dict],
    tabela: dict[str, PrecoReferencia],
    area_util_chapa_m2: float = AREA_UTIL_CHAPA_M2_PADRAO,
    pct_perda_corte: float = PCT_PERDA_CORTE_PADRAO,
) -> ResultadoCalculoProjeto:
    itens = _itens_flat(ambientes_json)
    resultado = ResultadoCalculoProjeto()
    indice_acabamento = indexar_precos_por_acabamento(tabela)

    # --- Chapas + fita: agrupar itens M2 por ACABAMENTO (espessura + material),
    # nao pelo REFERENCE completo -- o REFERENCE varia por tipo de peca mesmo
    # quando sai da mesma chapa (ver tabela_precos.chave_acabamento). ---
    area_por_acabamento: dict[tuple[int, str], float] = {}
    metros_fita_por_acabamento: dict[tuple[int, str], float] = {}
    referencia_exemplo_por_acabamento: dict[tuple[int, str], str] = {}

    for item in itens:
        if item.get("unidade") != "M2":
            continue
        ref = item.get("reference")
        chave = chave_acabamento(ref)
        if chave is None:
            # REFERENCE nao seguiu o padrao esperado -- trata como acabamento proprio (fallback)
            chave = (0, ref)
        referencia_exemplo_por_acabamento.setdefault(chave, ref)

        repeticao = item.get("repeticao", 1)
        quantidade_m2 = item.get("quantidade", 0.0)  # m2 da peca, ja calculado pelo Promob
        area_por_acabamento[chave] = area_por_acabamento.get(chave, 0.0) + quantidade_m2 * repeticao

        perimetro_m = _perimetro_fitavel_m(item.get("largura_mm"), item.get("altura_mm"), item.get("profundidade_mm"))
        metros_fita_por_acabamento[chave] = metros_fita_por_acabamento.get(chave, 0.0) + perimetro_m * repeticao

    for chave, area_total in area_por_acabamento.items():
        espessura, nome = chave
        rotulo = f"{espessura}mm {nome}" if espessura else nome
        preco_ref = indice_acabamento.get(chave)

        if preco_ref is None or preco_ref.preco_chapa_fechada is None:
            resultado.itens_sem_preco.append((referencia_exemplo_por_acabamento[chave], f"(chapa) {rotulo}", "SEM_PRECO_CHAPA_NA_TABELA"))
        else:
            area_com_perda = area_total * (1 + pct_perda_corte)
            num_chapas = math.ceil(area_com_perda / area_util_chapa_m2)
            custo = num_chapas * preco_ref.preco_chapa_fechada
            resultado.chapas.append(
                ResultadoChapasReferencia(
                    acabamento=rotulo,
                    area_total_m2=area_total,
                    area_com_perda_m2=area_com_perda,
                    num_chapas=num_chapas,
                    preco_chapa=preco_ref.preco_chapa_fechada,
                    custo_chapas=custo,
                )
            )

        metros_total = metros_fita_por_acabamento.get(chave, 0.0)
        if preco_ref is None or preco_ref.preco_fita_metro is None:
            resultado.itens_sem_preco.append((referencia_exemplo_por_acabamento[chave], f"(fita de borda) {rotulo}", "SEM_PRECO_FITA_NA_TABELA"))
        else:
            custo_fita = metros_total * preco_ref.preco_fita_metro
            resultado.fitas.append(
                ResultadoFitaReferencia(
                    acabamento=rotulo,
                    metros_total=metros_total,
                    preco_fita_metro=preco_ref.preco_fita_metro,
                    custo_fita=custo_fita,
                )
            )

    # --- Ferragens: itens UN ---
    for item in itens:
        if item.get("unidade") != "UN":
            continue
        custo, status = calcular_custo_item_ferragem(item, tabela)
        if status == "SEM_PRECO_NA_TABELA":
            resultado.itens_sem_preco.append((item.get("reference"), item.get("descricao"), status))
            continue
        # status "OK" ou "OK_INCLUIDO_NA_CHAPA" (custo=0 explicito, informado pelo usuario) -- ambos entram no total
        preco_ref = tabela.get(item.get("reference"))
        preco_unitario = preco_ref.preco_unitario_un if (preco_ref and preco_ref.preco_unitario_un is not None) else 0.0
        quantidade = item.get("repeticao", 1)
        resultado.ferragens.append(
            ResultadoFerragem(
                descricao=item.get("descricao"),
                reference=item.get("reference"),
                preco_unitario=preco_unitario,
                quantidade=quantidade,
                custo=custo,
                origem=item.get("origem", ""),
            )
        )

    return resultado
