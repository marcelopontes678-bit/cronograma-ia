"""Carrega a tabela de precos por referencia Promob (config/tabela_precos_referencia.xlsx)
e resolve o preco unitario de um item extraido pelo seu codigo REFERENCE.

Nao inventa preco para referencia ausente: item sem preco na tabela fica
sinalizado como pendente, nunca com custo zero ou estimado.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import openpyxl


@dataclass
class PrecoReferencia:
    reference: str
    codigo_interno: str
    descricao: str
    categoria: str
    espessura_mm: float | None
    unidade: str
    preco_unitario: float
    fornecedor: str


# Colunas da planilha (config/tabela_precos_referencia.xlsx), na ordem:
# REFERENCE, Codigo Interno, Descricao, Categoria, Espessura (mm), Unidade,
# Preco Unitario, Fornecedor, Data Atualizacao, Observacoes
def carregar_tabela_precos(caminho_xlsx: str | Path) -> dict[str, PrecoReferencia]:
    caminho_xlsx = Path(caminho_xlsx)
    if not caminho_xlsx.exists():
        raise FileNotFoundError(f"Tabela de precos nao encontrada: {caminho_xlsx}")

    wb = openpyxl.load_workbook(caminho_xlsx, data_only=True)
    ws = wb.active

    tabela: dict[str, PrecoReferencia] = {}
    for row in ws.iter_rows(min_row=5, max_row=ws.max_row):
        reference = row[0].value
        if not reference:
            continue
        preco = row[6].value
        if preco is None:
            continue
        espessura = row[4].value
        tabela[reference] = PrecoReferencia(
            reference=reference,
            codigo_interno=row[1].value or "",
            descricao=row[2].value or "",
            categoria=row[3].value or "",
            espessura_mm=float(espessura) if espessura is not None else None,
            unidade=row[5].value or "",
            preco_unitario=float(preco),
            fornecedor=row[7].value or "",
        )
    return tabela


def calcular_custo_item(item: dict, tabela: dict[str, PrecoReferencia]) -> tuple[float | None, str]:
    """Retorna (custo_material, status). custo_material e None quando a
    referencia nao esta na tabela de precos - o chamador NAO deve tratar
    isso como custo zero."""
    ref = item.get("reference")
    preco_ref = tabela.get(ref)
    if preco_ref is None:
        return None, "SEM_PRECO_NA_TABELA"

    quantidade = item.get("quantidade", 0.0)
    repeticao = item.get("repeticao", 1)
    unidade = item.get("unidade", "")

    if unidade == "UN":
        custo = preco_ref.preco_unitario * repeticao
    else:
        # M2, ML etc: quantidade ja vem calculada pelo Promob (ex: m2 da peca)
        custo = preco_ref.preco_unitario * quantidade * repeticao

    return custo, "OK"
