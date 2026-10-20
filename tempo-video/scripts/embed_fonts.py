"""Embute as fontes (public/fonts/*.woff2) como data: URL em src/generated/fontData.ts.

Evita requisições de rede dentro do Chrome durante a renderização — em máquinas sobrecarregadas
o carregamento por URL pode travar o delayRender. Rode de novo se trocar as fontes.
"""
import base64
from pathlib import Path

root = Path(__file__).resolve().parent.parent
names = [
    "cormorant-garamond-latin-400-normal", "cormorant-garamond-latin-500-normal", "cormorant-garamond-latin-600-normal",
    "cormorant-garamond-latin-400-italic", "cormorant-garamond-latin-500-italic",
    "inter-latin-400-normal", "inter-latin-500-normal", "inter-latin-600-normal", "inter-latin-700-normal",
    "inter-latin-800-normal", "inter-latin-900-normal",
]
lines = ["// GERADO por scripts/embed_fonts.py — não edite à mão.", "export const FONT_DATA: Record<string, string> = {"]
for n in names:
    b64 = base64.b64encode((root / "public" / "fonts" / f"{n}.woff2").read_bytes()).decode()
    lines.append(f'  "{n}": "data:font/woff2;base64,{b64}",')
lines.append("};")
out = root / "src" / "generated" / "fontData.ts"
out.write_text("\n".join(lines) + "\n")
print("ok", out.stat().st_size // 1024, "KB")
