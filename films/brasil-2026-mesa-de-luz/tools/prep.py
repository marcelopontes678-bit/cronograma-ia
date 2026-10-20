"""Texturas da mesa a partir dos arquivos reais em assets/raw e sources/.

- Fotos: reduzidas a no máximo 1600 px no lado maior (o tamanho de uma camada da textura), sem retoque.
- Registro do TSE: impressão dos campos do arquivo oficial br-c0001-e006257-u.json, com os valores
  exatamente como estão no arquivo. Grava assets/tex/tse.png e as caixas de cada linha em assets/tex/tse_lines.json
  (uv 0..1), para a "linha que acende".
Rodar: $LIB/.venv/bin/python -I tools/prep.py  (da pasta do filme)
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "assets", "raw")
TEX = os.path.join(HERE, "assets", "tex")
os.makedirs(TEX, exist_ok=True)
MAX = 1600

for name in ("congresso", "lula", "flavio", "urna", "stf"):
    src = os.path.join(RAW, name + ".jpg")
    if not os.path.exists(src):
        continue
    im = Image.open(src).convert("RGB")
    if name in ("lula", "flavio"):
        # mesmo formato para os dois retratos (largura/altura 0,77): só recorte, sem retoque
        a = 0.77
        if im.width / im.height > a:
            w = round(im.height * a); x0 = (im.width - w) // 2
            im = im.crop((x0, 0, x0 + w, im.height))
        else:
            im = im.crop((0, 0, im.width, round(im.width / a)))
    s = min(1.0, MAX / max(im.size))
    if s < 1:
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    im.save(os.path.join(TEX, name + ".jpg"), quality=93)
    print(name, im.size)

# --- impressão do registro do TSE ---
d = json.load(open(os.path.join(HERE, "sources", "tse_br-c0001-e006257-u.json"), encoding="utf-8"))
W, H = 1240, 1754
mono = lambda w, s: ImageFont.truetype(os.path.join(HERE, "fonts", f"IBMPlexMono-{w}.ttf"), s)
F, FB, FS = mono("Regular", 25), mono("SemiBold", 25), mono("Regular", 20)
im = Image.new("RGB", (W, H), "white")
dr = ImageDraw.Draw(im)
lines = {}
y = 110
X = 96


def put(key, text, font=F, gap=40):
    global y
    dr.text((X, y), text, fill=(18, 18, 20), font=font)
    bb = dr.textbbox((X, y), text, font=font)
    if key:
        lines[key] = [(bb[0] - 10) / W, (bb[1] - 8) / H, (bb[2] + 10) / W, (bb[3] + 8) / H]
    y += gap


put("head", "TRIBUNAL SUPERIOR ELEITORAL", FB)
put(None, "resultados.tse.jus.br", F, 34)
put("file", "oficial/ele2026/6257/dados/br/br-c0001-e006257-u.json", FS, 30)
put(None, "impressão dos campos do arquivo · valores literais", FS, 30)
put(None, "arquivo obtido em 20/10/2026 17:32 UTC (HTTP 200)", FS, 64)
put("ele", f"ele {d['ele']}   t {d['t']}   tpabr {d['tpabr']}   cdabr {d['cdabr']}")
put("dg", f"dg {d['dg']}   hg {d['hg']}")
put(None, f"carg  {d['carg'][0]['nmn']}", F, 64)
cands = [c for a in d["carg"][0]["agr"] for p in a["par"] for c in p["cand"]]
cands.sort(key=lambda c: -int(c["vap"]))
put(None, "n   nmu                          vap         pvap   st", FS, 36)
for c in cands:
    key = {"22": "c22", "13": "c13"}.get(c["n"])
    put(key, f"{c['n']:<3} {c['nmu'][:27]:<28} {int(c['vap']):>10}  {c['pvap']:>6}  {c['st']}", FS, 34)
y += 30
s, e, v = d["s"], d["e"], d["v"]
put("s", f"s   st {s['st']}   sa {s['sa']}   pst {s['pst']}")
put("e", f"e   te {e['te']}   c {e['c']}   pc {e['pc']}")
put("v", f"v   vv {v['vv']}   vb {v['vb']}   tvn {v['tvn']}")
y += 40
put(None, "n: número · nmu: nome na urna · vap: votos apurados", FS, 30)
put(None, "pvap: % dos votos válidos · st: situação", FS, 30)
put(None, "s: seções · e: eleitorado (c: comparecimento) · v: votos", FS, 30)
im.save(os.path.join(TEX, "tse.png"))
json.dump({"size": [W, H], "lines": lines}, open(os.path.join(TEX, "tse_lines.json"), "w"), indent=1)
print("tse", (W, H), sorted(lines))
sys.exit(0)
