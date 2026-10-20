"""Ambiente sonoro de "Tóquio à noite" (10 s, estéreo): chuva, cidade, carros, passos molhados e drone.
Os passos caem nos mesmos instantes do ciclo de caminhada do vídeo (phase = t*0.95, um passo a cada meio ciclo).
Saída: public/tokyo/ambience.mp3
"""
from pathlib import Path
import subprocess
import numpy as np
import soundfile as sf
from scipy import signal

ROOT = Path(__file__).resolve().parent.parent
SR, T = 44100, 10.0
N = int(SR * T)
rng = np.random.default_rng(5)
t = np.arange(N) / SR


def lp(x, fc, o=2): return signal.sosfilt(signal.butter(o, fc, "low", fs=SR, output="sos"), x, axis=-1)
def hp(x, fc, o=2): return signal.sosfilt(signal.butter(o, fc, "high", fs=SR, output="sos"), x, axis=-1)
def bp(x, a, b, o=2): return signal.sosfilt(signal.butter(o, [a, b], "band", fs=SR, output="sos"), x, axis=-1)


def put(buf, x, at, g=1.0, pan=0.5):
    i = int(at * SR)
    if i >= N: return
    j = min(N, i + x.shape[-1])
    seg = x[: j - i]
    buf[0, i:j] += seg * g * (1 - pan) * 1.4
    buf[1, i:j] += seg * g * pan * 1.4


out = np.zeros((2, N))

# chuva (duas fontes descorrelacionadas) + variação lenta
for ch in (0, 1):
    r = bp(rng.standard_normal(N), 1400, 9000)
    r *= 0.22 * (1 + 0.15 * np.sin(2 * np.pi * 0.23 * t + ch))
    out[ch] += r
# cidade: rumor grave + zumbido de rede elétrica
city = lp(rng.standard_normal(N), 140) * 0.9 + 0.05 * np.sin(2 * np.pi * 50 * t) + 0.03 * np.sin(2 * np.pi * 100 * t)
traffic = bp(rng.standard_normal(N), 180, 900) * (0.12 + 0.08 * np.sin(2 * np.pi * 0.17 * t + 1.0))
out += (city * 0.25 + traffic)[None, :]

# carros passando (whoosh com varredura de filtro e pan)
def car(at, direction=1, dur=2.2, g=0.55):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    y = np.zeros(n)
    seg = 1024
    for i in range(0, n - seg, seg):
        u = i / n
        fc = 250 + 900 * np.sin(np.pi * u)
        y[i:i + seg] = bp(x[i:i + seg], fc * 0.6, fc * 1.6)
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    y *= env
    pan = np.linspace(0.15, 0.85, n) if direction > 0 else np.linspace(0.85, 0.15, n)
    i = int(at * SR)
    j = min(N, i + n)
    out[0, i:j] += y[: j - i] * g * (1 - pan[: j - i])
    out[1, i:j] += y[: j - i] * g * pan[: j - i]

car(2.6, 1)
car(6.4, -1, 2.6, 0.5)

# passos na poça: 1 passo a cada 0,526 s (cadência do vídeo)
def step(side):
    n = int(0.22 * SR)
    tt = np.arange(n) / SR
    body = lp(rng.standard_normal(n), 900) * np.exp(-tt / 0.035)
    thump = np.sin(2 * np.pi * 95 * tt) * np.exp(-tt / 0.05)
    splash = bp(rng.standard_normal(n), 2500, 7000) * np.exp(-tt / 0.03) * 0.5
    return (body * 0.8 + thump * 0.6 + splash)

k = 0
while 0.26 + 0.526 * k < T - 0.5:
    put(out, step(k % 2), 0.26 + 0.526 * k, g=0.55, pan=0.42 + 0.16 * (k % 2))
    k += 1

# drone escuro (Lá menor) com LFO lento + notas esparsas
pad = np.zeros(N)
for f, g in ((55.0, 0.9), (82.4, 0.5), (110.0, 0.35), (130.8, 0.22)):
    for d in (-0.6, 0.0, 0.7):
        pad += g * signal.sawtooth(2 * np.pi * (f + d) * t, 0.5)
pad = lp(pad, 380 + 200 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.12 * t))[0]) if False else lp(pad, 520)
pad *= 0.018 * np.minimum(1, t / 2.5) * (1 + 0.2 * np.sin(2 * np.pi * 0.09 * t))
out += np.stack([pad, np.roll(pad, 31)])
for at, f in ((3.0, 220.0), (4.6, 261.6), (6.1, 329.6), (7.7, 196.0)):
    n = int(2.6 * SR)
    tt = np.arange(n) / SR
    note = sum(a * np.sin(2 * np.pi * f * h * tt) for h, a in ((1, 1), (2, 0.35), (3, 0.15))) * np.exp(-tt / 0.9)
    put(out, note * 0.05, at, 1.0, 0.5)

# sala (reverb curto) só para passos/carros/notas via mistura global leve
ir = rng.standard_normal((2, int(1.8 * SR))) * np.exp(-6.9 * np.arange(int(1.8 * SR)) / SR / 1.4)
ir = lp(ir, 4500)
ir /= np.abs(ir).sum(axis=1, keepdims=True) ** 0.5 * 9
wet = np.stack([signal.fftconvolve(out[c], ir[c])[:N] for c in (0, 1)])
mix = out + wet * 0.6
mix = hp(mix, 30)
mix *= np.minimum(1, t / 0.4) * np.minimum(1, (T - t) / 0.8)
mix = mix / np.abs(mix).max() * 0.82
tmp = ROOT / "audio" / "_tokyo.wav"
sf.write(tmp, mix.T.astype(np.float32), SR, subtype="FLOAT")
dst = ROOT / "public" / "tokyo" / "ambience.mp3"
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(tmp), "-t", str(T), "-codec:a", "libmp3lame", "-q:a", "2", str(dst)], check=True)
tmp.unlink()
print("ok", dst, f"{dst.stat().st_size/1e6:.2f} MB")
