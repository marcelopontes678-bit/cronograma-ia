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


def gerar_xlsx_projeto(
    resultado_calculo,  # calculo_projeto.ResultadoCalculoProjeto
    resultado_orcamento,  # orcamento_engine.ResultadoOrcamentoProjeto
    caminho_saida: str | Path,
    cliente: str = "",
    projeto: str = "",
) -> Path:
    """Gera o orcamento no modelo por chapa fechada + fita de borda + ferragens
    (em vez de peca por peca)."""
    caminho_saida = Path(caminho_saida)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orcamento"

    ws["A1"] = "Orcamento de Marcenaria"
    ws["A1"].font = Font(name=FONT, bold=True, size=16)
    ws.merge_cells("A1:E1")
    ws["A2"] = f"Cliente: {cliente or '-'}"
    ws["A3"] = f"Projeto: {projeto or '-'}"
    ws["A2"].font = Font(name=FONT, size=11)
    ws["A3"].font = Font(name=FONT, size=11)

    linha = 5
    ws.cell(row=linha, column=1, value="Divisor de Markup").font = Font(name=FONT, bold=True, size=10)
    ws.cell(row=linha, column=2, value=resultado_orcamento.divisor_markup).number_format = "0.0000"
    celula_divisor = f"$B${linha}"
    linha += 1
    ws.cell(row=linha, column=1, value="% Comissao de Vendas Aplicada").font = Font(name=FONT, bold=True, size=10)
    ws.cell(row=linha, column=2, value=resultado_orcamento.pct_comissao_vendas_aplicada).number_format = "0.0%"

    def escrever_secao(titulo, headers, linhas_dados, linha_inicio):
        l = linha_inicio
        ws.cell(row=l, column=1, value=titulo).font = Font(name=FONT, bold=True, size=12)
        l += 1
        for col, h in enumerate(headers, start=1):
            c = ws.cell(row=l, column=col, value=h)
            c.font = Font(name=FONT, bold=True, color=COR_HEADER_TEXTO)
            c.fill = PatternFill(start_color=COR_HEADER_BG, end_color=COR_HEADER_BG, fill_type="solid")
            c.border = BORDA
            c.alignment = Alignment(horizontal="center")
        l += 1
        primeira = l
        for linha_dados in linhas_dados:
            for col, val in enumerate(linha_dados, start=1):
                c = ws.cell(row=l, column=col, value=val)
                c.border = BORDA
                if isinstance(val, float):
                    c.number_format = MOEDA if headers[col - 1].startswith(("Custo", "Preco")) else "0.000"
            l += 1
        ultima = l - 1
        return l + 1, primeira, ultima

    linha += 2

    linhas_chapas = [
        [c.reference, c.area_total_m2, c.area_com_perda_m2, c.num_chapas, c.preco_chapa, c.custo_chapas]
        for c in resultado_calculo.chapas
    ]
    linha, p1, u1 = escrever_secao(
        "Chapas de MDF",
        ["Referencia", "Area Total (m2)", "Area c/ Perda (m2)", "Num Chapas", "Preco/Chapa (R$)", "Custo (R$)"],
        linhas_chapas,
        linha,
    )

    linhas_fitas = [[f.reference, f.metros_total, f.preco_fita_metro, f.custo_fita] for f in resultado_calculo.fitas]
    linha, p2, u2 = escrever_secao(
        "Fita de Borda",
        ["Referencia", "Metros Total", "Preco/Metro (R$)", "Custo (R$)"],
        linhas_fitas,
        linha,
    )

    linhas_ferragens = [[fe.descricao, fe.reference, fe.custo] for fe in resultado_calculo.ferragens]
    linha, p3, u3 = escrever_secao(
        "Ferragens / Componentes",
        ["Descricao", "Referencia", "Custo (R$)"],
        linhas_ferragens,
        linha,
    )

    linha += 1
    ws.cell(row=linha, column=1, value="Custo Material Total").font = Font(name=FONT, bold=True)
    f_custo = f"=SUM(F{p1}:F{u1})+SUM(D{p2}:D{u2})+SUM(C{p3}:C{u3})" if linhas_chapas or linhas_fitas or linhas_ferragens else 0
    ws.cell(row=linha, column=2, value=f_custo).number_format = MOEDA
    linha_custo_material = linha

    linha += 1
    ws.cell(row=linha, column=1, value="Preco Venda Material (x Markup)").font = Font(name=FONT, bold=True)
    ws.cell(row=linha, column=2, value=f"=B{linha_custo_material}*{celula_divisor}").number_format = MOEDA
    linha_venda = linha

    linha += 1
    ws.cell(row=linha, column=1, value="Mao de Obra").font = Font(name=FONT, bold=True)
    ws.cell(row=linha, column=2, value=resultado_orcamento.custo_mao_de_obra).number_format = MOEDA
    linha_mao_obra = linha

    linha += 1
    ws.cell(row=linha, column=1, value="TOTAL GERAL").font = Font(name=FONT, bold=True, size=12)
    ws.cell(row=linha, column=1).fill = PatternFill(start_color=COR_TOTAL_BG, end_color=COR_TOTAL_BG, fill_type="solid")
    c_total = ws.cell(row=linha, column=2, value=f"=B{linha_venda}+B{linha_mao_obra}")
    c_total.number_format = MOEDA
    c_total.font = Font(name=FONT, bold=True, size=12)
    c_total.fill = PatternFill(start_color=COR_TOTAL_BG, end_color=COR_TOTAL_BG, fill_type="solid")

    if resultado_calculo.itens_sem_preco:
        linha += 2
        ws.cell(row=linha, column=1, value=f"Pendencias sem preco na tabela ({len(resultado_calculo.itens_sem_preco)}) -- NAO incluidas no total:").font = Font(name=FONT, italic=True, color="C00000")
        linha += 1
        for ref, desc, motivo in resultado_calculo.itens_sem_preco:
            ws.cell(row=linha, column=1, value=f"  {motivo}: {ref} ({desc})").font = Font(name=FONT, italic=True, size=9, color="666666")
            linha += 1

    for i, w in enumerate([42, 18, 18, 14, 16, 14], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    wb.save(caminho_saida)
    return caminho_saida


if __name__ == "__main__":
    import argparse
    import json
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from calculo_projeto import calcular_projeto
    from orcamento_engine import calcular_orcamento_projeto, carregar_config
    from tabela_precos import carregar_tabela_precos

    parser = argparse.ArgumentParser(description="Gera orcamento final .xlsx (chapa/fita/ferragem) a partir de uma extracao Promob + tabela de precos.")
    parser.add_argument("arquivo_extracao_json", help="JSON gerado por extract_promob_xml.py")
    parser.add_argument("--tabela-precos", default=str(Path(__file__).resolve().parent.parent / "config" / "tabela_precos_referencia.xlsx"))
    parser.add_argument("--config", default=str(Path(__file__).resolve().parent.parent / "config" / "precificacao.json"))
    parser.add_argument("--faturamento-acumulado", type=float, required=True)
    parser.add_argument("--mao-de-obra", type=float, default=0.0)
    parser.add_argument("--cliente", default="")
    parser.add_argument("--saida", default=str(Path(__file__).resolve().parent.parent / "output" / "orcamento_final.xlsx"))
    args = parser.parse_args()

    data = json.load(open(args.arquivo_extracao_json, encoding="utf-8"))
    tabela = carregar_tabela_precos(args.tabela_precos)
    resultado_calculo = calcular_projeto(data, tabela)

    config = carregar_config(args.config)
    resultado_orcamento = calcular_orcamento_projeto(
        resultado_calculo.custo_material_total,
        config,
        args.faturamento_acumulado,
        custo_mao_de_obra=args.mao_de_obra,
    )

    caminho = gerar_xlsx_projeto(
        resultado_calculo,
        resultado_orcamento,
        args.saida,
        cliente=args.cliente,
        projeto=data[0]["nome"] if data else "",
    )
    print(f"Orcamento xlsx gerado: {caminho}")
    print(f"Custo material total: R${resultado_calculo.custo_material_total:.2f}")
    print(f"TOTAL (calculado em Python, para conferencia): R${resultado_orcamento.total:.2f}")
    if resultado_calculo.itens_sem_preco:
        print(f"ATENCAO: {len(resultado_calculo.itens_sem_preco)} pendencias sem preco na tabela (nao incluidas no total)")
