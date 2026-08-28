"""Gera o orcamento final em .xlsx a partir de um ResultadoOrcamento.

Usa formulas (nao valores fixos calculados em Python) para que o preco de
venda, o total por modulo e o total geral recalculem se o usuario editar
o custo de material ou a mao de obra diretamente na planilha.
"""
from __future__ import annotations

from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from orcamento_engine import ResultadoOrcamento

FONT = "Arial"
COR_HEADER_BG = "305496"
COR_HEADER_TEXTO = "FFFFFF"
COR_TOTAL_BG = "D9E1F2"
BORDA = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC"),
)
MOEDA = '$#,##0.00;($#,##0.00);"-"'


def gerar_xlsx(
    resultado: ResultadoOrcamento,
    caminho_saida: str | Path,
    cliente: str = "",
    projeto: str = "",
    faturamento_acumulado: float = 0.0,
) -> Path:
    caminho_saida = Path(caminho_saida)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orcamento"

    ws["A1"] = "Orcamento de Marcenaria"
    ws["A1"].font = Font(name=FONT, bold=True, size=16)
    ws.merge_cells("A1:F1")

    ws["A2"] = f"Cliente: {cliente or '-'}"
    ws["A2"].font = Font(name=FONT, size=11)
    ws["A3"] = f"Projeto: {projeto or '-'}"
    ws["A3"].font = Font(name=FONT, size=11)

    linha_params = 5
    ws.cell(row=linha_params, column=1, value="Divisor de Markup").font = Font(name=FONT, bold=True, size=10)
    ws.cell(row=linha_params, column=2, value=resultado.divisor_markup).number_format = "0.0000"
    ws.cell(row=linha_params + 1, column=1, value="% Comissao de Vendas Aplicada").font = Font(name=FONT, bold=True, size=10)
    ws.cell(row=linha_params + 1, column=2, value=resultado.pct_comissao_vendas_aplicada).number_format = "0.0%"
    ws.cell(row=linha_params + 2, column=1, value="Faturamento Acumulado Informado (R$)").font = Font(name=FONT, bold=True, size=10)
    ws.cell(row=linha_params + 2, column=2, value=faturamento_acumulado).number_format = MOEDA

    linha_cabecalho = linha_params + 4
    headers = ["Ambiente / Modulo", "Custo Material (R$)", "Divisor Markup", "Preco Venda Material (R$)", "Mao de Obra (R$)", "Preco Final (R$)"]
    for col, h in enumerate(headers, start=1):
        c = ws.cell(row=linha_cabecalho, column=col, value=h)
        c.font = Font(name=FONT, bold=True, color=COR_HEADER_TEXTO, size=11)
        c.fill = PatternFill(start_color=COR_HEADER_BG, end_color=COR_HEADER_BG, fill_type="solid")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDA

    celula_divisor = f"$B${linha_params}"
    linha_atual = linha_cabecalho + 1
    primeira_linha_dados = linha_atual
    for modulo in resultado.modulos:
        ws.cell(row=linha_atual, column=1, value=modulo.nome).border = BORDA
        cel_custo = ws.cell(row=linha_atual, column=2, value=modulo.custo_material)
        cel_custo.number_format = MOEDA
        cel_custo.border = BORDA

        cel_div = ws.cell(row=linha_atual, column=3, value=f"={celula_divisor}")
        cel_div.number_format = "0.0000"
        cel_div.border = BORDA

        col_custo_letra = get_column_letter(2)
        col_div_letra = get_column_letter(3)
        cel_venda = ws.cell(row=linha_atual, column=4, value=f"={col_custo_letra}{linha_atual}*{col_div_letra}{linha_atual}")
        cel_venda.number_format = MOEDA
        cel_venda.border = BORDA

        cel_mao_obra = ws.cell(row=linha_atual, column=5, value=modulo.custo_mao_de_obra)
        cel_mao_obra.number_format = MOEDA
        cel_mao_obra.border = BORDA

        col_venda_letra = get_column_letter(4)
        col_mao_obra_letra = get_column_letter(5)
        cel_final = ws.cell(row=linha_atual, column=6, value=f"={col_venda_letra}{linha_atual}+{col_mao_obra_letra}{linha_atual}")
        cel_final.number_format = MOEDA
        cel_final.border = BORDA

        linha_atual += 1

    ultima_linha_dados = linha_atual - 1

    ws.cell(row=linha_atual, column=1, value="TOTAL GERAL").font = Font(name=FONT, bold=True)
    ws.cell(row=linha_atual, column=1).fill = PatternFill(start_color=COR_TOTAL_BG, end_color=COR_TOTAL_BG, fill_type="solid")
    for col in range(2, 7):
        letra = get_column_letter(col)
        c = ws.cell(row=linha_atual, column=col, value=f"=SUM({letra}{primeira_linha_dados}:{letra}{ultima_linha_dados})")
        c.number_format = MOEDA
        c.font = Font(name=FONT, bold=True)
        c.fill = PatternFill(start_color=COR_TOTAL_BG, end_color=COR_TOTAL_BG, fill_type="solid")
        c.border = BORDA

    larguras = [42, 18, 14, 20, 16, 16]
    for i, w in enumerate(larguras, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.freeze_panes = ws.cell(row=linha_cabecalho + 1, column=1).coordinate

    wb.save(caminho_saida)
    return caminho_saida


if __name__ == "__main__":
    import argparse
    import json
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from orcamento_engine import Ambiente, ItemCusto, Modulo, calcular_orcamento, carregar_config
    from tabela_precos import calcular_custo_item, carregar_tabela_precos

    parser = argparse.ArgumentParser(description="Gera orcamento final .xlsx a partir de uma extracao Promob + tabela de precos.")
    parser.add_argument("arquivo_extracao_json", help="JSON gerado por extract_promob_xml.py")
    parser.add_argument("--tabela-precos", default=str(Path(__file__).resolve().parent.parent / "config" / "tabela_precos_referencia.xlsx"))
    parser.add_argument("--config", default=str(Path(__file__).resolve().parent.parent / "config" / "precificacao.json"))
    parser.add_argument("--faturamento-acumulado", type=float, required=True)
    parser.add_argument("--cliente", default="")
    parser.add_argument("--saida", default=str(Path(__file__).resolve().parent.parent / "output" / "orcamento_final.xlsx"))
    args = parser.parse_args()

    data = json.load(open(args.arquivo_extracao_json, encoding="utf-8"))
    tabela = carregar_tabela_precos(args.tabela_precos)

    ambientes = []
    for amb in data:
        ambiente = Ambiente(nome=amb["nome"])
        for mod in amb["modulos"]:
            modulo = Modulo(nome=mod["nome"])
            for it in mod["itens"]:
                custo, status = calcular_custo_item(it, tabela)
                if status != "OK":
                    continue
                modulo.itens.append(ItemCusto(descricao=it["descricao"], custo_material=custo, origem=it["origem"]))
            if modulo.itens:
                ambiente.modulos.append(modulo)
        ambientes.append(ambiente)

    config = carregar_config(args.config)
    resultado = calcular_orcamento(ambientes, config, args.faturamento_acumulado)

    caminho = gerar_xlsx(
        resultado,
        args.saida,
        cliente=args.cliente,
        projeto=data[0]["nome"] if data else "",
        faturamento_acumulado=args.faturamento_acumulado,
    )
    print(f"Orcamento xlsx gerado: {caminho}")
    print(f"TOTAL (calculado em Python, para conferencia): R${resultado.total:.2f}")
