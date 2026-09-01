"""Extractor de plantas em PDF (projetos de marcenaria exportados como PDF).

Duas estrategias, escolhidas automaticamente por arquivo:

1. EXTRACAO VETORIAL NATIVA (preferida): quando o PDF tem texto/objetos
   vetoriais reais (nao e so uma imagem escaneada), usa pdfplumber para
   pegar texto com coordenadas (pagina, x, y) e PyMuPDF (fitz) para pegar
   os desenhos vetoriais (linhas/retangulos que formam os moveis), com
   rastreabilidade ate pagina + coordenada.

2. FALLBACK ASSISTIDO POR IMAGEM: quando a pagina nao tem texto extraivel
   (PDF escaneado, so imagem), a pagina e renderizada como imagem em alta
   resolucao e fica marcada como "precisa_assistencia" -- este script NAO
   tenta OCR automatico de dimensoes/medidas sozinho, porque adivinhar
   numeros de uma planta escaneada sem revisao humana e perigoso para
   orcamento. A imagem fica salva para o usuario (ou um passo posterior
   assistido) revisar e digitar os dados manualmente.

Nunca inventa dimensoes ou modulos que nao estao no arquivo.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber


@dataclass
class TextoExtraido:
    texto: str
    pagina: int
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class LinhaVetorial:
    pagina: int
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class PaginaExtraida:
    pagina: int
    tem_texto_vetorial: bool
    textos: list[TextoExtraido] = field(default_factory=list)
    linhas: list[LinhaVetorial] = field(default_factory=list)
    precisa_assistencia: bool = False
    imagem_fallback: str | None = None  # caminho do PNG renderizado, quando precisa_assistencia=True


def _pagina_tem_texto(pdfplumber_page) -> bool:
    texto = pdfplumber_page.extract_text()
    return bool(texto and texto.strip())


def _extrair_textos(pdfplumber_page, numero_pagina: int) -> list[TextoExtraido]:
    palavras = pdfplumber_page.extract_words()
    return [
        TextoExtraido(
            texto=w["text"],
            pagina=numero_pagina,
            x0=w["x0"],
            y0=w["top"],
            x1=w["x1"],
            y1=w["bottom"],
        )
        for w in palavras
    ]


def _extrair_linhas_vetoriais(fitz_page, numero_pagina: int) -> list[LinhaVetorial]:
    linhas = []
    for desenho in fitz_page.get_drawings():
        for item in desenho["items"]:
            tipo = item[0]
            if tipo == "l":  # linha reta: ("l", p1, p2)
                p1, p2 = item[1], item[2]
                linhas.append(LinhaVetorial(pagina=numero_pagina, x0=p1.x, y0=p1.y, x1=p2.x, y1=p2.y))
            elif tipo == "re":  # retangulo: ("re", Rect)
                r = item[1]
                linhas.append(LinhaVetorial(pagina=numero_pagina, x0=r.x0, y0=r.y0, x1=r.x1, y1=r.y1))
    return linhas


def _renderizar_fallback(fitz_page, numero_pagina: int, pasta_saida: Path, dpi: int = 300) -> str:
    pasta_saida.mkdir(parents=True, exist_ok=True)
    zoom = dpi / 72
    matriz = fitz.Matrix(zoom, zoom)
    pix = fitz_page.get_pixmap(matrix=matriz)
    caminho_png = pasta_saida / f"pagina_{numero_pagina}_escaneada.png"
    pix.save(str(caminho_png))
    return str(caminho_png)


def extrair(caminho_pdf: str | Path, pasta_fallback: str | Path = "output/pdf_fallback_imagens") -> list[PaginaExtraida]:
    caminho_pdf = Path(caminho_pdf)
    if not caminho_pdf.exists():
        raise FileNotFoundError(f"Arquivo PDF nao encontrado: {caminho_pdf}")

    pasta_fallback = Path(pasta_fallback)
    paginas_extraidas: list[PaginaExtraida] = []

    with pdfplumber.open(caminho_pdf) as pdf_plumber_doc:
        doc_fitz = fitz.open(str(caminho_pdf))

        for i, pagina_plumber in enumerate(pdf_plumber_doc.pages):
            numero_pagina = i + 1
            pagina_fitz = doc_fitz[i]

            tem_texto = _pagina_tem_texto(pagina_plumber)

            if tem_texto:
                textos = _extrair_textos(pagina_plumber, numero_pagina)
                linhas = _extrair_linhas_vetoriais(pagina_fitz, numero_pagina)
                paginas_extraidas.append(
                    PaginaExtraida(
                        pagina=numero_pagina,
                        tem_texto_vetorial=True,
                        textos=textos,
                        linhas=linhas,
                    )
                )
            else:
                caminho_imagem = _renderizar_fallback(pagina_fitz, numero_pagina, pasta_fallback)
                paginas_extraidas.append(
                    PaginaExtraida(
                        pagina=numero_pagina,
                        tem_texto_vetorial=False,
                        precisa_assistencia=True,
                        imagem_fallback=caminho_imagem,
                    )
                )

        doc_fitz.close()

    return paginas_extraidas


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrai texto/vetores de uma planta em PDF (com fallback para PDF escaneado).")
    parser.add_argument("arquivo_pdf")
    parser.add_argument("--saida", help="Caminho para salvar JSON normalizado (opcional)")
    parser.add_argument("--pasta-fallback", default="output/pdf_fallback_imagens")
    args = parser.parse_args()

    paginas = extrair(args.arquivo_pdf, args.pasta_fallback)
    saida_json = json.dumps([asdict(p) for p in paginas], ensure_ascii=False, indent=2)

    for p in paginas:
        if p.tem_texto_vetorial:
            print(f"Pagina {p.pagina}: VETORIAL - {len(p.textos)} textos, {len(p.linhas)} linhas/retangulos")
        else:
            print(f"Pagina {p.pagina}: ESCANEADA - precisa assistencia, imagem em {p.imagem_fallback}")

    print()
    print(saida_json[:3000])
    print("... (truncado)" if len(saida_json) > 3000 else "")

    if args.saida:
        Path(args.saida).write_text(saida_json, encoding="utf-8")
        print(f"\nJSON completo salvo em: {args.saida}")
