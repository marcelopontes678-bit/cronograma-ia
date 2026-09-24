"""Renderiza paginas de um ou mais PDFs em imagens PNG para envio ao Claude
Vision.

Reaproveita a mesma abordagem (PyMuPDF/fitz) ja validada em
extractors/extract_pdf_plant.py -- so muda o destino: aqui vira
base64 para a API de mensagens, la vira fallback de PDF escaneado.

Um job pode ter mais de um arquivo de origem (ex: planta tecnica + render
3D do mesmo ambiente, ambos PDF), para o extrator cruzar as referencias
visuais na mesma chamada ao Claude. Cada pagina/recorte carrega
`arquivo_indice` (posicao do arquivo na lista enviada, 0-indexed) e
`nome_arquivo` (nome original) para que o bounding_box de um modulo
continue rastreavel ate o arquivo+pagina corretos mesmo com varios PDFs
no mesmo job."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


@dataclass
class PaginaRenderizada:
    numero: int  # 1-indexed, LOCAL ao arquivo (nao um contador global do job)
    arquivo_indice: int  # posicao (0-indexed) do arquivo de origem na lista enviada
    nome_arquivo: str  # nome original do arquivo, para rotular o contexto enviado ao Claude
    largura_px: int
    altura_px: int
    caminho_arquivo: Path
    media_type: str = "image/png"

    def base64(self) -> str:
        return base64.standard_b64encode(self.caminho_arquivo.read_bytes()).decode("ascii")


@dataclass
class RecortePagina:
    """Um quadrante de alta resolucao de uma pagina densa (varias vistas
    empacotadas numa prancha so). Uma pagina grande precisa ser reduzida
    para caber no limite de imagem da API (ver _zoom_que_cabe), o que dilui
    a resolucao e torna texto pequeno (legendas de acabamento, cotas finas)
    ilegivel. Cada quadrante e renderizado separadamente, entao perde menos
    resolucao."""

    pagina_numero: int  # local ao arquivo, mesmo significado de PaginaRenderizada.numero
    arquivo_indice: int
    nome_arquivo: str
    rotulo: str  # ex: "superior-esquerdo"
    bbox_pagina_normalizado: list[int]  # [y_min, x_min, y_max, x_max] 0-1000, relativo a PAGINA INTEIRA
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

# Limite de imagem que o modelo le sem reamostrar (Sonnet 5: lado maior
# 2576px, ~3.75MP) -- valido ate 20 imagens por chamada; acima disso a API
# recusa (400) imagem com lado maior que 2000px (ver MAX_IMAGENS_POR_CHAMADA
# em orcamento_vision_extractor.py). Toda imagem e renderizada JA dentro
# desse limite, para que o tamanho em pixels que o modelo ve seja
# exatamente o que informamos a ele -- o bounding_box volta em pixels dessa
# imagem e e convertido para 0-1000 no codigo.
LADO_MAX_PX = 2576
AREA_MAX_PX = 3_700_000
DPI_RECORTE = 300
_GRID_ROTULOS = {
    (0, 0): "superior-esquerdo",
    (0, 1): "superior-direito",
    (1, 0): "inferior-esquerdo",
    (1, 1): "inferior-direito",
}
_SOBREPOSICAO = 0.1  # fracao da pagina que os quadrantes vizinhos compartilham, para nao cortar um modulo bem na divisa


def _zoom_que_cabe(largura_pt: float, altura_pt: float, dpi: int) -> float:
    """Zoom do fitz (pixels por ponto) no DPI pedido, reduzido o quanto
    for preciso para a imagem caber em LADO_MAX_PX e AREA_MAX_PX."""
    zoom = dpi / 72
    # -4px de margem: o fitz arredonda as bordas do clip para fora e pode
    # gerar 1-2px a mais que o calculado.
    zoom = min(zoom, (LADO_MAX_PX - 4) / max(largura_pt, altura_pt))
    zoom = min(zoom, (AREA_MAX_PX / (largura_pt * altura_pt)) ** 0.5)
    return zoom


def _gerar_recortes_pagina(
    pagina: "fitz.Page", numero: int, arquivo_indice: int, nome_arquivo: str, pasta_saida: Path
) -> list[RecortePagina]:
    """Gera os 4 quadrantes de alta resolucao de uma pagina, cada um
    renderizado direto do PDF (nao recortado do PNG ja rasterizado) para
    nao herdar a perda de nitidez do render em resolucao mais baixa."""
    rect = pagina.rect
    recortes: list[RecortePagina] = []

    for (linha, coluna), rotulo in _GRID_ROTULOS.items():
        x0f = 0.0 if coluna == 0 else 0.5 - _SOBREPOSICAO
        x1f = 0.5 + _SOBREPOSICAO if coluna == 0 else 1.0
        y0f = 0.0 if linha == 0 else 0.5 - _SOBREPOSICAO
        y1f = 0.5 + _SOBREPOSICAO if linha == 0 else 1.0

        clip = fitz.Rect(x0f * rect.width, y0f * rect.height, x1f * rect.width, y1f * rect.height)
        zoom = _zoom_que_cabe(clip.width, clip.height, DPI_RECORTE)
        pix = pagina.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip)
        caminho_png = pasta_saida / f"pagina_{numero:03d}_recorte_{rotulo}.png"
        pix.save(str(caminho_png))

        recortes.append(
            RecortePagina(
                pagina_numero=numero,
                arquivo_indice=arquivo_indice,
                nome_arquivo=nome_arquivo,
                rotulo=rotulo,
                bbox_pagina_normalizado=[round(y0f * 1000), round(x0f * 1000), round(y1f * 1000), round(x1f * 1000)],
                largura_px=pix.width,
                altura_px=pix.height,
                caminho_arquivo=caminho_png,
            )
        )
    return recortes


def _renderizar_paginas_de_um_arquivo(
    caminho_pdf: Path,
    arquivo_indice: int,
    pasta_saida: Path,
    dpi: int,
) -> tuple[list[PaginaRenderizada], list[RecortePagina]]:
    nome_arquivo = caminho_pdf.name

    paginas_renderizadas: list[PaginaRenderizada] = []
    recortes: list[RecortePagina] = []
    doc = fitz.open(str(caminho_pdf))
    try:
        for i in range(len(doc)):
            pagina = doc[i]
            zoom = _zoom_que_cabe(pagina.rect.width, pagina.rect.height, dpi)
            pix = pagina.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            caminho_png = pasta_saida / f"pagina_{i + 1:03d}.png"
            pix.save(str(caminho_png))
            paginas_renderizadas.append(
                PaginaRenderizada(
                    numero=i + 1,
                    arquivo_indice=arquivo_indice,
                    nome_arquivo=nome_arquivo,
                    largura_px=pix.width,
                    altura_px=pix.height,
                    caminho_arquivo=caminho_png,
                )
            )
            if zoom < dpi / 72:  # a pagina foi reduzida para caber -- recortes recuperam a resolucao
                recortes.extend(
                    _gerar_recortes_pagina(pagina, i + 1, arquivo_indice, nome_arquivo, pasta_saida)
                )
    finally:
        doc.close()

    return paginas_renderizadas, recortes


def renderizar_paginas(
    caminhos_pdf: list[str | Path],
    pasta_saida: str | Path,
    dpi: int = DPI_PADRAO,
) -> tuple[list[PaginaRenderizada], list[RecortePagina]]:
    """Renderiza as paginas de UM OU MAIS PDFs em PNG. Cada arquivo grava
    suas paginas numa subpasta propria (`arquivo_{indice}/`) para nao
    colidir numeracao entre arquivos (pagina 1 do arquivo 0 e pagina 1 do
    arquivo 1 sao PNGs diferentes). Toda imagem e renderizada dentro do
    limite de LADO_MAX_PX/AREA_MAX_PX; paginas que precisaram ser reduzidas
    para caber (tipico de pranchas A3 com varias vistas empacotadas)
    tambem ganham recortes em alta resolucao (ver RecortePagina). Retorna (paginas, recortes), listas
    achatadas de todos os arquivos, na ordem em que foram enviados."""
    if not caminhos_pdf:
        raise ValueError("Nenhum arquivo PDF informado para renderizar.")

    pasta_saida = Path(pasta_saida)

    todas_paginas: list[PaginaRenderizada] = []
    todos_recortes: list[RecortePagina] = []
    for arquivo_indice, caminho in enumerate(caminhos_pdf):
        caminho_pdf = Path(caminho)
        if not caminho_pdf.exists():
            raise FileNotFoundError(f"PDF nao encontrado: {caminho_pdf}")

        pasta_arquivo = pasta_saida / f"arquivo_{arquivo_indice}"
        pasta_arquivo.mkdir(parents=True, exist_ok=True)

        paginas, recortes = _renderizar_paginas_de_um_arquivo(caminho_pdf, arquivo_indice, pasta_arquivo, dpi)
        todas_paginas.extend(paginas)
        todos_recortes.extend(recortes)

    return todas_paginas, todos_recortes
