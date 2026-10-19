"""Gera 4 quadros de granulação de filme (512x512, cinza) em public/grain/. Determinístico."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

out = Path(__file__).resolve().parent.parent / "public" / "grain"
out.mkdir(parents=True, exist_ok=True)
for i in range(4):
    rng = np.random.default_rng(100 + i)
    a = rng.normal(128, 46, (512, 512)).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(a, "L").filter(ImageFilter.GaussianBlur(0.55))
    im.save(out / f"grain{i}.png", optimize=True)
print("ok", [p.name for p in sorted(out.iterdir())])
