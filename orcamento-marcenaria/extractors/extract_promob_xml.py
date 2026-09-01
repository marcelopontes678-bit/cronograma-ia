"""Extractor de arquivos XML exportados do Promob (listagem de montados).

Le o XML de "Listagem_montados" do Promob e normaliza para a estrutura
unica de dados do skill: ambientes -> modulos -> itens, com dimensoes e
acabamento (REFERENCE), mantendo rastreabilidade ate o GUID/UNIQUEID do
elemento original no XML.

IMPORTANTE: este tipo de exportacao do Promob NAO traz preco em R$ (nao
ha atributo de valor monetario nos ITEMs, so codigo de referencia de
material/acabamento). O preco de cada item precisa vir de uma tabela de
precos por referencia (ainda nao implementada) antes de alimentar o
orcamento_engine. Este extractor entrega apenas a geometria e o
acabamento normalizados, nunca um custo inventado.
"""
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ItemExtraido:
    descricao: str
    reference: str
    unidade: str
    largura_mm: float | None
    altura_mm: float | None
    profundidade_mm: float | None
    quantidade: float
    repeticao: int
    origem: str  # rastreabilidade: GUID/UNIQUEID do ITEM no XML


@dataclass
class ModuloExtraido:
    nome: str
    origem: str  # GUID do ITEM pai (composicao/armario)
    itens: list[ItemExtraido] = field(default_factory=list)


@dataclass
class AmbienteExtraido:
    nome: str
    origem: str  # GUID do AMBIENT
    modulos: list[ModuloExtraido] = field(default_factory=list)


def _float_attr(elem: ET.Element, attr: str) -> float | None:
    val = elem.attrib.get(attr)
    if val is None or val == "":
        return None
    try:
        return float(val.replace(",", "."))
    except ValueError:
        return None


def _extrair_item(item_elem: ET.Element) -> ItemExtraido:
    guid = item_elem.attrib.get("GUID", "")
    uniqueid = item_elem.attrib.get("UNIQUEID", "")
    origem = f"GUID={guid} UNIQUEID={uniqueid}"
    return ItemExtraido(
        descricao=item_elem.attrib.get("DESCRIPTION", ""),
        reference=item_elem.attrib.get("REFERENCE", ""),
        unidade=item_elem.attrib.get("UNIT", ""),
        largura_mm=_float_attr(item_elem, "WIDTH"),
        altura_mm=_float_attr(item_elem, "HEIGHT"),
        profundidade_mm=_float_attr(item_elem, "DEPTH"),
        quantidade=_float_attr(item_elem, "QUANTITY") or 0.0,
        repeticao=int(item_elem.attrib.get("REPETITION", "1") or "1"),
        origem=origem,
    )


def _extrair_modulo(item_pai_elem: ET.Element) -> ModuloExtraido:
    """Um ITEM de topo (armario/composicao) vira um Modulo; seus sub-ITEMS
    (elemento ITEMS aninhado) viram os itens de material do modulo. Se o
    proprio item de topo nao tiver sub-itens, ele mesmo entra como item
    unico do modulo."""
    guid = item_pai_elem.attrib.get("GUID", "")
    modulo = ModuloExtraido(
        nome=item_pai_elem.attrib.get("DESCRIPTION", ""),
        origem=f"GUID={guid}",
    )

    sub_items_elem = item_pai_elem.find("ITEMS")
    if sub_items_elem is not None and len(sub_items_elem.findall("ITEM")) > 0:
        for sub_item_elem in sub_items_elem.findall("ITEM"):
            modulo.itens.append(_extrair_item(sub_item_elem))
    else:
        modulo.itens.append(_extrair_item(item_pai_elem))

    return modulo


def extrair(caminho_xml: str | Path) -> list[AmbienteExtraido]:
    caminho_xml = Path(caminho_xml)
    if not caminho_xml.exists():
        raise FileNotFoundError(f"Arquivo XML nao encontrado: {caminho_xml}")

    tree = ET.parse(caminho_xml)
    root = tree.getroot()

    ambientes: list[AmbienteExtraido] = []
    for ambient_elem in root.findall(".//AMBIENT"):
        ambiente = AmbienteExtraido(
            nome=ambient_elem.attrib.get("DESCRIPTION", ""),
            origem=f"GUID={ambient_elem.attrib.get('GUID', '')}",
        )
        categories_elem = ambient_elem.find("CATEGORIES")
        if categories_elem is None:
            ambientes.append(ambiente)
            continue

        for category_elem in categories_elem.findall("CATEGORY"):
            items_elem = category_elem.find("ITEMS")
            if items_elem is None:
                continue
            for item_pai_elem in items_elem.findall("ITEM"):
                ambiente.modulos.append(_extrair_modulo(item_pai_elem))

        ambientes.append(ambiente)

    return ambientes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrai geometria/materiais de um XML de listagem Promob.")
    parser.add_argument("arquivo_xml")
    parser.add_argument("--saida", help="Caminho para salvar JSON normalizado (opcional)")
    args = parser.parse_args()

    ambientes = extrair(args.arquivo_xml)
    saida_json = json.dumps([asdict(a) for a in ambientes], ensure_ascii=False, indent=2)

    total_modulos = sum(len(a.modulos) for a in ambientes)
    total_itens = sum(len(m.itens) for a in ambientes for m in a.modulos)
    print(f"Ambientes extraidos: {len(ambientes)}")
    print(f"Modulos extraidos: {total_modulos}")
    print(f"Itens extraidos: {total_itens}")
    print()
    print(saida_json[:4000])
    print("... (truncado)" if len(saida_json) > 4000 else "")

    if args.saida:
        Path(args.saida).write_text(saida_json, encoding="utf-8")
        print(f"\nJSON completo salvo em: {args.saida}")
