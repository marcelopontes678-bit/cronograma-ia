"""Extractor de arquivos DXF (do Promob, ou de um DWG convertido via
convert_dwg.py) usando a biblioteca ezdxf.

IMPORTANTE - honestidade sobre o que este extractor sabe: o schema de
blocos/layers que o Promob usa ao exportar DXF (nomes de bloco por modulo,
atributos de dimensao/acabamento) ainda nao foi confirmado contra um DXF
real exportado do Promob (so testamos contra DXFs genericos de CAD, via
LibreDWG). Por isso este extractor NAO tenta adivinhar quais blocos sao
"modulos" Promob -- ele extrai tudo de forma generica e rastreavel
(blocos inseridos, geometria por camada, textos/atributos), para que a
etapa seguinte (mapear isso para Ambiente/Modulo/Item) seja feita com
um DXF real do Promob em maos, confirmando o schema com o usuario.

Rastreabilidade: cada elemento carrega layer + handle (identificador
unico do DXF) + coordenadas, apontando de volta ao arquivo original.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import ezdxf


@dataclass
class BlocoInserido:
    """Uma instancia de bloco (INSERT) no DXF -- candidato a "modulo" ou
    "componente", mas o mapeamento exato depende do schema real do Promob."""
    nome_bloco: str
    layer: str
    x: float
    y: float
    z: float
    escala_x: float
    escala_y: float
    escala_z: float
    rotacao_graus: float
    atributos: dict[str, str]  # ATTRIB dentro do INSERT, se houver (chave=tag, valor=texto)
    origem: str  # handle DXF


@dataclass
class GeometriaExtraida:
    tipo: str  # LINE, LWPOLYLINE, CIRCLE, ARC, etc.
    layer: str
    pontos: list[tuple[float, float]]
    origem: str  # handle DXF


@dataclass
class TextoExtraido:
    texto: str
    layer: str
    x: float
    y: float
    origem: str  # handle DXF


@dataclass
class DxfExtraido:
    layers: list[str]
    blocos: list[BlocoInserido] = field(default_factory=list)
    geometrias: list[GeometriaExtraida] = field(default_factory=list)
    textos: list[TextoExtraido] = field(default_factory=list)


def _extrair_atributos_insert(insert) -> dict[str, str]:
    atributos = {}
    if insert.attribs:
        for attrib in insert.attribs:
            atributos[attrib.dxf.tag] = attrib.dxf.text
    return atributos


def extrair(caminho_dxf: str | Path) -> DxfExtraido:
    caminho_dxf = Path(caminho_dxf)
    if not caminho_dxf.exists():
        raise FileNotFoundError(f"Arquivo DXF nao encontrado: {caminho_dxf}")

    doc = ezdxf.readfile(str(caminho_dxf))
    msp = doc.modelspace()

    layers = [layer.dxf.name for layer in doc.layers]
    resultado = DxfExtraido(layers=layers)

    for entidade in msp:
        tipo = entidade.dxftype()
        layer = entidade.dxf.layer
        handle = entidade.dxf.handle

        if tipo == "INSERT":
            resultado.blocos.append(
                BlocoInserido(
                    nome_bloco=entidade.dxf.name,
                    layer=layer,
                    x=entidade.dxf.insert.x,
                    y=entidade.dxf.insert.y,
                    z=entidade.dxf.insert.z,
                    escala_x=entidade.dxf.xscale,
                    escala_y=entidade.dxf.yscale,
                    escala_z=entidade.dxf.zscale,
                    rotacao_graus=entidade.dxf.rotation,
                    atributos=_extrair_atributos_insert(entidade),
                    origem=f"handle={handle}",
                )
            )
        elif tipo in ("LINE",):
            pontos = [(entidade.dxf.start.x, entidade.dxf.start.y), (entidade.dxf.end.x, entidade.dxf.end.y)]
            resultado.geometrias.append(GeometriaExtraida(tipo=tipo, layer=layer, pontos=pontos, origem=f"handle={handle}"))
        elif tipo in ("LWPOLYLINE",):
            pontos = [(p[0], p[1]) for p in entidade.get_points()]
            resultado.geometrias.append(GeometriaExtraida(tipo=tipo, layer=layer, pontos=pontos, origem=f"handle={handle}"))
        elif tipo in ("CIRCLE", "ARC"):
            centro = entidade.dxf.center
            pontos = [(centro.x, centro.y)]
            resultado.geometrias.append(GeometriaExtraida(tipo=tipo, layer=layer, pontos=pontos, origem=f"handle={handle}"))
        elif tipo in ("TEXT", "MTEXT"):
            texto = entidade.dxf.text if tipo == "TEXT" else entidade.text
            pos = entidade.dxf.insert
            resultado.textos.append(TextoExtraido(texto=texto, layer=layer, x=pos.x, y=pos.y, origem=f"handle={handle}"))

    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrai blocos/geometria/textos de um DXF (Promob ou DWG convertido).")
    parser.add_argument("arquivo_dxf")
    parser.add_argument("--saida", help="Caminho para salvar JSON normalizado (opcional)")
    args = parser.parse_args()

    resultado = extrair(args.arquivo_dxf)
    saida_json = json.dumps(asdict(resultado), ensure_ascii=False, indent=2)

    print(f"Layers: {len(resultado.layers)}")
    print(f"Blocos (INSERT) extraidos: {len(resultado.blocos)}")
    print(f"Geometrias (LINE/LWPOLYLINE/CIRCLE/ARC) extraidas: {len(resultado.geometrias)}")
    print(f"Textos extraidos: {len(resultado.textos)}")
    print()
    print(saida_json[:3000])
    print("... (truncado)" if len(saida_json) > 3000 else "")

    if args.saida:
        Path(args.saida).write_text(saida_json, encoding="utf-8")
        print(f"\nJSON completo salvo em: {args.saida}")
