"""Embute só os glifos japoneses usados nos letreiros (Noto Sans JP 900, SIL OFL, via @fontsource).

A fonte do fontsource vem em ~125 pedaços por faixa unicode. Este script acha os pedaços que contêm os
caracteres de TEXT, recorta cada um só para esses glifos (fontTools) e grava src/generated/jpFontData.ts
com data: URL + unicode-range. Rode de novo se mudar os letreiros.
"""
import base64, io, re
from pathlib import Path
from fontTools.ttLib import woff2, TTFont
from fontTools import subset

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "node_modules" / "@fontsource" / "noto-sans-jp"
TEXT = "ラーメン居酒屋カラオケホテル薬局焼鳥喫茶24時間営業寿司バー新宿酒場夜東京"
need = {ord(c) for c in TEXT}

def parse_ranges(s):
    cps = set()
    for part in s.split(","):
        part = part.strip().replace("U+", "")
        if "-" in part:
            a, b = part.split("-"); cps.update(range(int(a, 16), int(b, 16) + 1))
        elif part:
            cps.add(int(part, 16))
    return cps

css = (PKG / "900.css").read_text()
faces = re.findall(r"@font-face\s*{(.*?)}", css, re.S)
out = []
covered = set()
for f in faces:
    m_url = re.search(r"url\(\./files/([^)]+\.woff2)\)", f) or re.search(r"url\(([^)]+?\.woff2)\)", f)
    m_rng = re.search(r"unicode-range:\s*([^;]+);", f)
    if not m_url or not m_rng:
        continue
    hit = need & parse_ranges(m_rng.group(1))
    if not hit:
        continue
    src = PKG / "files" / Path(m_url.group(1)).name
    font = TTFont(str(src))
    opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["*"]
    sub = subset.Subsetter(opts); sub.populate(unicodes=sorted(hit)); sub.subset(font)
    buf = io.BytesIO(); font.flavor = "woff2"; font.save(buf)
    rng = ",".join(f"U+{c:x}" for c in sorted(hit))
    out.append((base64.b64encode(buf.getvalue()).decode(), rng))
    covered |= hit

missing = need - covered
assert not missing, f"faltando: {''.join(map(chr, missing))}"
lines = ["// GERADO por scripts/embed_jp_font.py — não edite à mão.", "export const JP_FONT: { url: string; unicodeRange: string }[] = ["]
for b64, rng in out:
    lines.append(f'  {{ url: "data:font/woff2;base64,{b64}", unicodeRange: "{rng}" }},')
lines.append("];")
dst = ROOT / "src" / "generated" / "jpFontData.ts"
dst.write_text("\n".join(lines) + "\n")
print("ok", len(out), "pedaços,", dst.stat().st_size // 1024, "KB,", len(need), "caracteres")
