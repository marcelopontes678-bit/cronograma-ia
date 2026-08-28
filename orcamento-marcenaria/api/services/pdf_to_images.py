"""Renderiza paginas de um PDF em imagens PNG para envio ao Claude Vision.

Reaproveita a mesma abordagem (PyMuPDF/fitz) ja validada em
extractors/extract_pdf_plant.py -- so muda o destino: aqui vira
base64 para a API de mensagens, la vira fallback de PDF escaneado.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


@dataclass
class PaginaRenderizada:
    numero: int  # 1-indexed
    largura_px: int
    altura_px: int
    caminho_arquivo: Path
    media_type: str = "image/png"

    def base64(self) -> str:
        return base64.standard_b64encode(self.caminho_arquivo.read_bytes()).decode("ascii")


# Limite pratico: Claude aceita imagens grandes, mas o custo/tempo de
# processamento cresce com a resolucao. 200 DPI e suficiente para ler
# cotas de desenho tecnico sem gerar imagens desnecessariamente grandes.
DPI_PADRAO = 200


def renderizar_paginas(
    caminho_pdf: str | Path,
    pasta_saida: str | Path,
    dpi: int = DPI_PADRAO,
    paginas: list[int] | None = None,
) -> list[PaginaRenderizada]:
    """Renderiza paginas do PDF em PNG. `paginas` (1-indexed) filtra
    quais paginas renderizar; None renderiza todas."""
    caminho_pdf = Path(caminho_pdf)
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    if not caminho_pdf.exists():
        raise FileNotFoundError(f"PDF nao encontrado: {caminho_pdf}")

    zoom = dpi / 72
    matriz = fitz.Matrix(zoom, zoom)

    resultado: list[PaginaRenderizada] = []
    doc = fitz.open(str(caminho_pdf))
    try:
        indices = range(len(doc)) if paginas is None else [p - 1 for p in paginas]
        for i in indices:
            if i < 0 or i >= len(doc):
                raise ValueError(f"Pagina {i + 1} fora do intervalo do PDF (1-{len(doc)}).")
            pagina = doc[i]
            pix = pagina.get_pixmap(matrix=matriz)
            caminho_png = pasta_saida / f"pagina_{i + 1:03d}.png"
            pix.save(str(caminho_png))
            resultado.append(
                PaginaRenderizada(
                    numero=i + 1,
                    largura_px=pix.width,
                    altura_px=pix.height,
                    caminho_arquivo=caminho_png,
                )
            )
    finally:
        doc.close()

    return resultado
