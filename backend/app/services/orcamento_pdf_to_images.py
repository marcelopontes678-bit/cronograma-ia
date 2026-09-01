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


@dataclass
class RecortePagina:
    """Um quadrante de alta resolucao de uma pagina densa (varias vistas
    empacotadas numa prancha so). A API do Claude reamostra imagens acima
    de ~1568px no lado maior antes do modelo "ver" -- uma pagina inteira
    nesse formato dilui a resolucao entre os quadrantes, tornando texto
    pequeno (legendas de acabamento, cotas finas) ilegivel mesmo
    renderizando o PDF em alta resolucao no nosso lado. Recortar em
    quadrantes e reamostrar cada um separadamente evita essa diluicao."""

    pagina_numero: int
    rotulo: str  # ex: "superior-esquerdo"
    bbox_pagina_normalizado: list[int]  # [y_min, x_min, y_max, x_max] 0-1000, relativo a PAGINA INTEIRA
    caminho_arquivo: Path
    media_type: str = "image/png"

    def base64(self) -> str:
        return base64.standard_b64encode(self.caminho_arquivo.read_bytes()).decode("ascii")


# Limite pratico: Claude aceita imagens grandes, mas o custo/tempo de
# processamento cresce com a resolucao. 200 DPI e suficiente para ler
# cotas de desenho tecnico sem gerar imagens desnecessariamente grandes.
DPI_PADRAO = 200

# Acima desse tamanho (px, no lado maior) a pagina inteira ja seria
# reamostrada pela API do Claude -- so entao vale a pena gerar recortes.
LIMIAR_TILING_PX = 1600
DPI_RECORTE = 300
_GRID_ROTULOS = {
    (0, 0): "superior-esquerdo",
    (0, 1): "superior-direito",
    (1, 0): "inferior-esquerdo",
    (1, 1): "inferior-direito",
}
_SOBREPOSICAO = 0.1  # fracao da pagina que os quadrantes vizinhos compartilham, para nao cortar um modulo bem na divisa


def _gerar_recortes_pagina(pagina: "fitz.Page", numero: int, pasta_saida: Path) -> list[RecortePagina]:
    """Gera os 4 quadrantes de alta resolucao de uma pagina, cada um
    renderizado direto do PDF (nao recortado do PNG ja rasterizado) para
    nao herdar a perda de nitidez do render em resolucao mais baixa."""
    rect = pagina.rect
    recortes: list[RecortePagina] = []
    zoom = DPI_RECORTE / 72
    matriz = fitz.Matrix(zoom, zoom)

    for (linha, coluna), rotulo in _GRID_ROTULOS.items():
        x0f = 0.0 if coluna == 0 else 0.5 - _SOBREPOSICAO
        x1f = 0.5 + _SOBREPOSICAO if coluna == 0 else 1.0
        y0f = 0.0 if linha == 0 else 0.5 - _SOBREPOSICAO
        y1f = 0.5 + _SOBREPOSICAO if linha == 0 else 1.0

        clip = fitz.Rect(x0f * rect.width, y0f * rect.height, x1f * rect.width, y1f * rect.height)
        pix = pagina.get_pixmap(matrix=matriz, clip=clip)
        caminho_png = pasta_saida / f"pagina_{numero:03d}_recorte_{rotulo}.png"
        pix.save(str(caminho_png))

        recortes.append(
            RecortePagina(
                pagina_numero=numero,
                rotulo=rotulo,
                bbox_pagina_normalizado=[round(y0f * 1000), round(x0f * 1000), round(y1f * 1000), round(x1f * 1000)],
                caminho_arquivo=caminho_png,
            )
        )
    return recortes


def renderizar_paginas(
    caminho_pdf: str | Path,
    pasta_saida: str | Path,
    dpi: int = DPI_PADRAO,
    paginas: list[int] | None = None,
) -> tuple[list[PaginaRenderizada], list[RecortePagina]]:
    """Renderiza paginas do PDF em PNG. `paginas` (1-indexed) filtra quais
    paginas renderizar; None renderiza todas. Paginas densas (acima de
    LIMIAR_TILING_PX no lado maior -- tipico de pranchas com varias vistas
    empacotadas) tambem ganham recortes em alta resolucao (ver
    RecortePagina), porque a API do Claude reamostra a pagina inteira
    antes de qualquer recorte ajudar. Retorna (paginas, recortes)."""
    caminho_pdf = Path(caminho_pdf)
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    if not caminho_pdf.exists():
        raise FileNotFoundError(f"PDF nao encontrado: {caminho_pdf}")

    zoom = dpi / 72
    matriz = fitz.Matrix(zoom, zoom)

    paginas_renderizadas: list[PaginaRenderizada] = []
    recortes: list[RecortePagina] = []
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
            paginas_renderizadas.append(
                PaginaRenderizada(
                    numero=i + 1,
                    largura_px=pix.width,
                    altura_px=pix.height,
                    caminho_arquivo=caminho_png,
                )
            )
            if max(pix.width, pix.height) > LIMIAR_TILING_PX:
                recortes.extend(_gerar_recortes_pagina(pagina, i + 1, pasta_saida))
    finally:
        doc.close()

    return paginas_renderizadas, recortes
