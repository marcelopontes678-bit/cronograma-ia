"""Leitura dos currículos: PDF, DOCX, TXT e MD.

PDF escaneado (imagem, sem texto selecionável) não é descartado: quando o
texto extraído é curto demais, o PDF original é enviado ao Claude como
documento, e ele lê a imagem.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

EXTENSOES = {".pdf", ".docx", ".txt", ".md"}
MIN_CARACTERES_TEXTO = 200
MAX_BYTES_PDF = 20 * 1024 * 1024


@dataclass
class Documento:
    caminho: Path
    texto: str = ""
    pdf_base64: str | None = None  # preenchido só para PDF sem texto


def listar_curriculos(pasta: Path) -> list[Path]:
    return sorted(
        p for p in pasta.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSOES
    )


def _texto_pdf(caminho: Path) -> str:
    from pypdf import PdfReader

    leitor = PdfReader(str(caminho))
    return "\n".join((pagina.extract_text() or "") for pagina in leitor.pages)


def _texto_docx(caminho: Path) -> str:
    import docx

    d = docx.Document(str(caminho))
    partes = [p.text for p in d.paragraphs]
    for tabela in d.tables:
        for linha in tabela.rows:
            partes.append(" | ".join(c.text for c in linha.cells))
    return "\n".join(partes)


def ler(caminho: Path) -> Documento:
    ext = caminho.suffix.lower()
    if ext == ".pdf":
        texto = _texto_pdf(caminho).strip()
        if len(texto) >= MIN_CARACTERES_TEXTO:
            return Documento(caminho, texto=texto)
        if caminho.stat().st_size > MAX_BYTES_PDF:
            raise ValueError("PDF escaneado grande demais (limite 20 MB).")
        dados = base64.standard_b64encode(caminho.read_bytes()).decode()
        return Documento(caminho, texto=texto, pdf_base64=dados)
    if ext == ".docx":
        return Documento(caminho, texto=_texto_docx(caminho).strip())
    if ext in {".txt", ".md"}:
        return Documento(caminho, texto=caminho.read_text(encoding="utf-8", errors="replace").strip())
    raise ValueError(f"Formato não suportado: {ext}")
