"""Pontos-alvo das partículas: a palavra DESIGN rasterizada em Inter 900 (arquivo local) e amostrada."""
import io, json
from pathlib import Path
import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent.parent
f = TTFont(str(root / "public/fonts/inter-latin-900-normal.woff2"))
f.flavor = None
buf = io.BytesIO(); f.save(buf); buf.seek(0)
font = ImageFont.truetype(buf, 230)
W, H = 1080, 420
im = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(im)
bbox = d.textbbox((0, 0), "DESIGN", font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
d.text(((W - tw) / 2 - bbox[0], (H - th) / 2 - bbox[1]), "DESIGN", font=font, fill=255)
a = np.array(im)
step = 8
pts = [(x, y) for y in range(0, H, step) for x in range(0, W, step) if a[y, x] > 140]
rng = np.random.default_rng(3)
idx = rng.choice(len(pts), size=min(950, len(pts)), replace=False)
sel = [[int(pts[i][0]), int(pts[i][1] + 960 - H / 2)] for i in sorted(idx)]
(root / "src/reel/data/designPoints.json").write_text(json.dumps(sel))
print("ok", len(sel), "pontos; texto", tw, "x", th)
