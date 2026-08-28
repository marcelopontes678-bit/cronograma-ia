"""Carrega a tabela de precos por referencia Promob (config/tabela_precos_referencia.xlsx).

Modelo de precificacao por REFERENCE (acabamento/material):
- Chapas de MDF (itens com unidade M2): precificadas por CHAPA FECHADA
  (preco_chapa_fechada, R$/chapa de 2750x1830mm), nao por m2 da peca --
  ver engine/calculo_projeto.py para o calculo de quantas chapas o
  projeto consome.
- Fita de borda (mesmas referencias de chapa): precificada por METRO
  (preco_fita_metro, R$/m), calculada pelo perimetro das pecas.
- Ferragens/componentes (itens com unidade UN): mantem preco por unidade
  (preco_unitario_un), multiplicado pela quantidade/repeticao do item.

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
    preco_unitario_un: float | None       # para itens UN (ferragens/componentes)
    preco_chapa_fechada: float | None     # para itens M2 (chapa MDF, preco da chapa 2750x1830mm inteira)
    preco_fita_metro: float | None        # para itens M2 (fita de borda do mesmo acabamento, R$/m)
    fornecedor: str


# Colunas da planilha (config/tabela_precos_referencia.xlsx), na ordem:
# REFERENCE, Codigo Interno, Descricao, Categoria, Espessura (mm), Unidade,
# Preco Unitario UN (R$), Preco Chapa Fechada (R$), Preco Fita de Borda (R$/m),
# Fornecedor, Data Atualizacao, Observacoes
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

        preco_un = row[6].value
        preco_chapa = row[7].value
        preco_fita = row[8].value
        espessura = row[4].value

        if preco_un is None and preco_chapa is None and preco_fita is None:
            continue

        tabela[reference] = PrecoReferencia(
            reference=reference,
            codigo_interno=row[1].value or "",
            descricao=row[2].value or "",
            categoria=row[3].value or "",
            espessura_mm=float(espessura) if espessura is not None else None,
            unidade=row[5].value or "",
            preco_unitario_un=float(preco_un) if preco_un is not None else None,
            preco_chapa_fechada=float(preco_chapa) if preco_chapa is not None else None,
            preco_fita_metro=float(preco_fita) if preco_fita is not None else None,
            fornecedor=row[9].value or "",
        )
    return tabela


def calcular_custo_item_ferragem(item: dict, tabela: dict[str, PrecoReferencia]) -> tuple[float | None, str]:
    """Para itens de unidade UN (ferragens/componentes). Retorna (custo, status).
    custo e None quando a referencia nao tem preco_unitario_un cadastrado."""
    ref = item.get("reference")
    preco_ref = tabela.get(ref)
    if preco_ref is None or preco_ref.preco_unitario_un is None:
        return None, "SEM_PRECO_NA_TABELA"

    repeticao = item.get("repeticao", 1)
    custo = preco_ref.preco_unitario_un * repeticao
    return custo, "OK"
