"""Extractor de projetos SketchUp (.skp) via EXPORTACAO MANUAL ASSISTIDA.

Decisao (confirmada com o usuario): este skill NUNCA faz parsing direto do
binario .skp. Em vez disso, o usuario exporta os componentes do modelo pelo
proprio SketchUp usando "File > Generate Report..." (Relatorio de
Quantidades), que gera um CSV/TXT com uma linha por instancia de componente
e colunas de nome, dimensoes e contagem. Este extractor le esse relatorio.

Como gerar o relatorio no SketchUp:
  1. File > Generate Report...
  2. Marque para incluir todas as instancias de componentes (nao so definicoes).
  3. Inclua os atributos: Name (ou Definition Name), Length, Width, Height, Count.
  4. Exporte como CSV.

Isso evita depender de bibliotecas fragil de parsing .skp binario e nao
exige o SketchUp Pro instalado neste ambiente -- o usuario roda a
exportacao na maquina dele, onde o SketchUp ja esta instalado.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


class RelatorioSkpInvalidoError(Exception):
    pass


# Nomes de coluna aceitos (SketchUp usa nomes diferentes conforme o idioma
# e a versao); o extractor tenta casar por qualquer um desses aliases.
ALIASES_COLUNAS = {
    "nome": ["Name", "Definition Name", "Nome", "Nome da Definição"],
    "comprimento": ["Length", "Comprimento"],
    "largura": ["Width", "Largura"],
    "altura": ["Height", "Altura"],
    "quantidade": ["Count", "Quantity", "Quantidade"],
    "material": ["Material", "Front Material", "Material Frontal"],
}


@dataclass
class ItemSkpExtraido:
    nome: str
    comprimento_mm: float | None
    largura_mm: float | None
    altura_mm: float | None
    quantidade: int
    material: str
    origem: str  # rastreabilidade: linha do relatorio CSV


def _mapear_colunas(cabecalho: list[str]) -> dict[str, str]:
    mapeamento: dict[str, str] = {}
    for chave_interna, aliases in ALIASES_COLUNAS.items():
        for alias in aliases:
            if alias in cabecalho:
                mapeamento[chave_interna] = alias
                break
    if "nome" not in mapeamento:
        raise RelatorioSkpInvalidoError(
            f"Nenhuma coluna de nome encontrada no relatorio. Colunas esperadas: {ALIASES_COLUNAS['nome']}. "
            f"Colunas presentes: {cabecalho}"
        )
    return mapeamento


def _float_ou_none(valor: str | None) -> float | None:
    if valor is None or valor.strip() == "":
        return None
    valor_limpo = valor.replace('"', "").replace("mm", "").replace(",", ".").strip()
    try:
        return float(valor_limpo)
    except ValueError:
        return None


def extrair(caminho_relatorio: str | Path) -> list[ItemSkpExtraido]:
    caminho_relatorio = Path(caminho_relatorio)
    if not caminho_relatorio.exists():
        raise FileNotFoundError(
            f"Relatorio nao encontrado: {caminho_relatorio}. "
            f"Gere-o no SketchUp via File > Generate Report... e exporte como CSV."
        )

    with open(caminho_relatorio, "r", encoding="utf-8-sig", newline="") as f:
        # SketchUp Generate Report normalmente usa tab como separador; tenta detectar.
        amostra = f.read(4096)
        f.seek(0)
        try:
            dialeto = csv.Sniffer().sniff(amostra, delimiters=",\t;")
        except csv.Error:
            dialeto = csv.excel

        leitor = csv.DictReader(f, dialect=dialeto)
        if not leitor.fieldnames:
            raise RelatorioSkpInvalidoError("Relatorio CSV vazio ou sem cabecalho.")

        mapeamento = _mapear_colunas(leitor.fieldnames)

        itens: list[ItemSkpExtraido] = []
        for numero_linha, linha in enumerate(leitor, start=2):  # linha 1 = cabecalho
            nome = linha.get(mapeamento["nome"], "").strip()
            if not nome:
                continue

            quantidade_raw = linha.get(mapeamento.get("quantidade", ""), "1")
            try:
                quantidade = int(float(quantidade_raw)) if quantidade_raw else 1
            except ValueError:
                quantidade = 1

            itens.append(
                ItemSkpExtraido(
                    nome=nome,
                    comprimento_mm=_float_ou_none(linha.get(mapeamento.get("comprimento", ""))),
                    largura_mm=_float_ou_none(linha.get(mapeamento.get("largura", ""))),
                    altura_mm=_float_ou_none(linha.get(mapeamento.get("altura", ""))),
                    quantidade=quantidade,
                    material=linha.get(mapeamento.get("material", ""), "").strip(),
                    origem=f"linha={numero_linha} arquivo={caminho_relatorio.name}",
                )
            )

    return itens


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extrai itens de um relatorio de componentes exportado do SketchUp (File > Generate Report)."
    )
    parser.add_argument("arquivo_relatorio")
    parser.add_argument("--saida", help="Caminho para salvar JSON normalizado (opcional)")
    args = parser.parse_args()

    itens = extrair(args.arquivo_relatorio)
    saida_json = json.dumps([asdict(i) for i in itens], ensure_ascii=False, indent=2)

    print(f"Itens extraidos: {len(itens)}")
    print()
    print(saida_json[:3000])
    print("... (truncado)" if len(saida_json) > 3000 else "")

    if args.saida:
        Path(args.saida).write_text(saida_json, encoding="utf-8")
        print(f"\nJSON completo salvo em: {args.saida}")
