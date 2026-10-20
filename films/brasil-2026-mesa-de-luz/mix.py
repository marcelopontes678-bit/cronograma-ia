"""Trilha, foley, ambiente e voz → out/mix.wav (48 kHz, estéreo).
Lê out/events.json (exportado de window.EV) e narration-timeline.json (falas medidas).
Rodar da raiz da biblioteca: .venv/bin/python films/brasil-2026/mix.py
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
import soxr

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get("LIB") or os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, LIB)
from core.audio import sampler as S  # noqa: E402
from core.audio.sfx import SR, add, bp, click, clack, compress, ding, env_exp, hp, limit, lp, noise, t_, whoosh  # noqa: E402

S.seed(7)
EVJ = json.load(open(os.path.join(HERE, "out", "events.json")))
DUR = EVJ["dur"]
N = int(DUR * SR)
NAR = json.load(open(os.path.join(HERE, "narration-timeline.json")))
SPEECH = NAR["speech"]


def st():
    return np.zeros((N, 2), np.float32)


# ---------------- ambiente: reator da mesa de luz ----------------
amb = st()
tt = np.arange(N) / SR
hum = (np.sin(2 * np.pi * 100 * tt) * .5 + np.sin(2 * np.pi * 200 * tt) * .22 + np.sin(2 * np.pi * 300 * tt) * .12)
hum = hum * (1 + .04 * np.sin(2 * np.pi * .37 * tt))
room = lp(noise(DUR), 900) * .35
off_at = next(e["t"] for e in EVJ["ev"] if e["type"] == "off")
lvl = np.ones(N)
i0, i1 = int(off_at * SR), int((off_at + .5) * SR)
lvl[i0:i1] = np.linspace(1, .18, i1 - i0)
lvl[i1:] = .18
bed = (hum * .55 + room) * lvl
# dentro da foto da urna: o ar de uma sala mais quente substitui o zumbido
room_at = next(e["t"] for e in EVJ["ev"] if e["type"] == "room")
w = np.clip((tt - (room_at - 1.0)) / 1.0, 0, 1) * np.clip((26.9 - tt) / .4, 0, 1)
warm = lp(noise(DUR), 500) * .9 + hp(lp(noise(DUR), 3000), 1200) * .08
bed = bed * (1 - .7 * w) + warm * w * .8
amb[:, 0] = bed
amb[:, 1] = bed * .97

# ---------------- foley ----------------
fx = st()


def paper(d=.45, v=1.0):
    x = bp(noise(d), 1500, 7000) * np.sin(np.linspace(0, np.pi, int(round(d * SR)))) ** 1.5
    return x * .35 * v


def pen(v=1.0):
    d = .38
    x = bp(noise(d), 2500, 8000) * (0.6 + 0.4 * np.abs(np.sin(np.linspace(0, 23, int(round(d * SR))))))
    return x * env_exp(d, .25) * .5 * v


def lens_ring(v=1.0, f=2650):
    d = 1.2
    x = sum(np.sin(2 * np.pi * f * k * t_(d)) * a for k, a in ((1, 1), (2.76, .35), (5.4, .12)))
    return x * env_exp(d, .35) * .10 * v


def beep(v=1.0):
    out = np.zeros(int(.6 * SR))
    for k, (f, a) in enumerate(((1180, .0), (1180, .15), (1180, .3))):
        b = np.sin(2 * np.pi * f * t_(.09)) * np.hanning(int(round(.09 * SR)))
        s = int(a * SR)
        out[s:s + len(b)] += b
    return out * .10 * v


for e in EVJ["ev"]:
    t, ty = e["t"], e["type"]
    if ty == "land":
        add(fx, clack(1.3, .55), t, .8)
        add(fx, lens_ring(1.0), t + .01, 1.0)
    elif ty == "lift":
        add(fx, click(1.6, .5), t, .45)
        add(fx, lens_ring(.6, 3100), t, .7)
    elif ty == "glide":
        add(fx, paper(.6), t, .9, -.2)
    elif ty == "rise":
        add(fx, whoosh(.9, .5), t, .35)
    elif ty == "into":
        add(fx, whoosh(1.1, .7), t, .45)
    elif ty == "card":
        add(fx, click(1.0, .45), t, .5, .15)
        add(fx, paper(.3, .5), t, .6, .15)
    elif ty in ("click", "click2"):
        add(fx, click(1.3, .4), t, .45, -.1)
        if ty == "click2":
            add(fx, click(1.25, .4), t + .004, .45, .1)
    elif ty == "tick":
        add(fx, click(2.2, .3), t, .35)
    elif ty == "pen":
        add(fx, pen(), t, .8, .1)
    elif ty == "beep":
        add(fx, beep(), t, .8)
    elif ty == "off":
        add(fx, click(.7, .8), t, .8)
        add(fx, clack(.6, .4), t + .05, .4)

# ---------------- música (72 bpm; 1 compasso de 4 = 3,333 s) ----------------
q = 60 / 72
ev = []
P = lambda t, inst, p, d, v, pan=0, g=1.0: ev.append((t, inst, p, d, v, pan, g))
# abertura: nota grave quando a câmera sobe da lente; vidro quando a lupa levanta
P(0.4, "piano", "D2", 3.0, .42, -.1)
P(0.4, "piano", "D3", 3.0, .32, .1)
P(2.6, "glockenspiel", "A6", 1.0, .18, .3)
# responsabilização: piano esparso que se adensa (semínimas → colcheias), Ré menor
chords = [("D3", ["D4", "F4", "A4", "F4"]), ("A#2", ["D4", "F4", "A#4", "F4"]), ("F2", ["C4", "F4", "A4", "F4"])]
t0 = 5.0
for bar, (bass, arp) in enumerate(chords):
    bt = t0 + bar * 4 * q * 0.8
    P(bt, "piano", bass, 2.6, .36, -.15)
    step = q if bar == 0 else q / 2
    n = int(round(4 * q * 0.8 / step))
    for i in range(n):
        P(bt + i * step, "piano", arp[i % 4], step * 1.5, .25 + .03 * bar, .15)
P(6.0, "vibraphone_bowed", "A5", 2.4, .35, .25)
P(9.55, "vibraphone_bowed", "F5", 2.0, .25, -.25)
# lado a lado: pedal neutro de cordas, sem melodia
P(13.0, "cellos", "D3", 7.8, .38, -.2)
P(13.4, "violas", "A3", 7.4, .30, .2)
P(17.2, "contrabass", "D2", 3.6, .28, 0)
# voto: o piano sobe de registro
up = ["D5", "F5", "A5", "D6"]
for i in range(int((23.6 - 20.9) / (q / 2))):
    P(20.9 + i * q / 2, "piano", up[i % 4], q, .22, .2)
P(23.6, "glockenspiel", "D6", 1.6, .22, -.2)
P(24.6, "vibraphone_bowed", "A5", 2.0, .3, .2)
P(24.6, "violins", "A4", 2.0, .18, .2)
# silêncio 26,6–27,4 · veredito: Ré maior aberto
for p, v in (("D2", .42), ("D3", .36), ("A3", .3), ("F#4", .28), ("A4", .24)):
    P(27.45, "piano", p, 2.5, v, 0)
P(27.5, "cellos", "D3", 2.5, .32, -.2)
P(27.5, "violins", "F#4", 2.4, .2, .2)
P(27.5, "vibraphone_bowed", "D5", 2.4, .3, 0)
mus = S.render([dict(t=e[0], inst=e[1], pitch=e[2], dur=e[3], vel=e[4], pan=e[5]) for e in ev], dur=DUR, master=False)
mus = S.room(mus, size=.45, mix=.2)
mus = mus[:N] if len(mus) >= N else np.vstack([mus, np.zeros((N - len(mus), 2), np.float32)])
# silêncio real antes do veredito
g = np.ones(N)
a, b = int(26.55 * SR), int(27.4 * SR)
g[a:b] = 0
mus = mus * g[:, None]

# ---------------- voz ----------------
v, vsr = sf.read(os.path.join(HERE, "audio", "narration.wav"), dtype="float32")
if v.ndim > 1:
    v = v.mean(1)
v = soxr.resample(v, vsr, SR)
v = compress(hp(v, 80), thr=.2, ratio=3.0)
v = v[:N] if len(v) >= N else np.concatenate([v, np.zeros(N - len(v))])
voice = np.stack([v, v], 1).astype(np.float32)

# ---------------- balanço e ducking ----------------
rms = lambda x: float(np.sqrt(np.mean(x[np.abs(x).max(1) > 1e-4] ** 2) + 1e-12))
vr = rms(voice)
mus *= (vr / rms(mus)) * 10 ** (-11 / 20)
fx *= (vr / max(rms(fx), 1e-9)) * 10 ** (-10 / 20)
amb *= (vr / rms(amb)) * 10 ** (-27 / 20)
duck = np.zeros(N)
for s in SPEECH:
    duck = np.maximum(duck, np.clip(np.minimum((tt - s["start"] + .15) / .15, (s["end"] + .35 - tt) / .35), 0, 1))
mus *= (1 - .45 * duck)[:, None]

mix = voice + mus + fx + amb
mix = hp(mix.T, 38).T
mix = limit(mix.astype(np.float32), .9)
os.makedirs(os.path.join(HERE, "out", "stems"), exist_ok=True)
for name, x in (("voice", voice), ("music", mus), ("fx", fx), ("amb", amb)):
    sf.write(os.path.join(HERE, "out", "stems", name + ".wav"), x.astype(np.float32), SR)
sf.write(os.path.join(HERE, "out", "mix.wav"), mix, SR)
print("mix", mix.shape, "peak", float(np.abs(mix).max()))
open(os.path.join(HERE, "out", "instruments.json"), "w").write(json.dumps(sorted({e[1] for e in ev})))
