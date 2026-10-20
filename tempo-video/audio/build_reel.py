"""Trilha do showreel: 15 s, 120 BPM, Ré menor. Cada evento visual tem um som no frame exato.
Saída: public/reel/track.mp3
"""
from pathlib import Path
import subprocess
import numpy as np
import soundfile as sf
from scipy import signal

ROOT = Path(__file__).resolve().parent.parent
SR, T = 44100, 15.0
N = int(SR * T)
rng = np.random.default_rng(42)
B = 0.5  # batida (120 BPM)


def tt(n): return np.arange(n) / SR
def lp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, "low", fs=SR, output="sos"), x, axis=-1)
def hp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, "high", fs=SR, output="sos"), x, axis=-1)
def bp(x, a, b): return signal.sosfilt(signal.butter(2, [a, b], "band", fs=SR, output="sos"), x)
def hz(m): return 440 * 2 ** ((m - 69) / 12)


mix = np.zeros((2, N))
def put(x, at, g=1.0, pan=0.5):
    i = int(round(at * SR))
    if i >= N or i + len(x) <= 0: return
    j = min(N, i + len(x))
    mix[0, i:j] += x[: j - i] * g * (1 - pan) * 1.4
    mix[1, i:j] += x[: j - i] * g * pan * 1.4


# ---------------------------------------------------------------- instrumentos
def kick(g=1.0):
    t = tt(int(0.32 * SR)); f = 45 + 120 * np.exp(-t / 0.028)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16) * g + lp(rng.standard_normal(len(t)), 3000) * np.exp(-t / 0.004) * 0.3
def clap():
    t = tt(int(0.22 * SR)); n = bp(rng.standard_normal(len(t)), 900, 5000)
    env = sum(np.exp(-np.maximum(0, t - d) / 0.012) * (t >= d) for d in (0, 0.011, 0.022)) * 0.5 + np.exp(-t / 0.07) * 0.5
    return n * env
def hat(open_=False):
    t = tt(int((0.12 if open_ else 0.04) * SR)); return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t / (0.05 if open_ else 0.012))
def pluck(m, dur=0.35, bright=0.6):
    t = tt(int(dur * SR)); f = hz(m)
    x = sum((1 / k) * np.exp(-k * (1 - bright)) * np.sin(2 * np.pi * f * k * t) for k in range(1, 9))
    return x * np.exp(-t / (dur * 0.35)) * (1 - np.exp(-t / 0.002))
def blip(m, dur=0.12):
    t = tt(int(dur * SR)); f = hz(m) * (1 + 0.6 * np.exp(-t / 0.01))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.04)
def bass(m, dur=0.24):
    t = tt(int(dur * SR)); f = hz(m)
    x = signal.sawtooth(2 * np.pi * f * t) * 0.5 + np.sin(2 * np.pi * f * t)
    return lp(x, 600) * np.minimum(1, (dur - t) / 0.02) * (1 - np.exp(-t / 0.004))
def stab(ms, dur=0.3, cut=2200):
    t = tt(int(dur * SR))
    x = sum(signal.sawtooth(2 * np.pi * hz(m) * (1 + d) * t) for m in ms for d in (-0.004, 0.004))
    return lp(x, cut) * np.exp(-t / (dur * 0.4)) / len(ms)
def noise_sweep(dur, f0, f1, rev=False):
    n = int(dur * SR); x = rng.standard_normal(n); y = np.zeros(n); seg = 512
    for i in range(0, n - seg, seg):
        u = i / n; fc = f0 * (f1 / f0) ** u
        y[i:i + seg] = bp(x[i:i + seg], max(40, fc * 0.6), min(SR / 2 - 200, fc * 1.6))
    env = np.linspace(0, 1, n) ** 2 if not rev else np.linspace(1, 0, n) ** 2
    return y * env
def boom(g=1.0):
    t = tt(int(1.2 * SR)); f = 38 + 60 * np.exp(-t / 0.06)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45) + lp(rng.standard_normal(len(t)), 900) * np.exp(-t / 0.05) * 0.5) * g
def bloop(m):
    t = tt(int(0.18 * SR)); f = hz(m) * (0.7 + 0.6 * (t / t[-1]))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / t[-1]) ** 0.6
def pad(ms, dur):
    t = tt(int(dur * SR))
    x = sum(signal.sawtooth(2 * np.pi * hz(m) * (1 + d) * t, 0.5) for m in ms for d in (-0.003, 0, 0.003))
    return lp(x, 1800) * np.minimum(1, t / 0.02) * np.exp(-t / (dur * 0.45)) / len(ms)

# ---------------------------------------------------------------- 0–1,5 s: ponto quicando
put(blip(86), 0.0, 0.5); put(blip(81), 0.5, 0.45); put(blip(74), 1.0, 0.45)
put(noise_sweep(0.6, 300, 6000), 0.9, 0.35)
# ---------------------------------------------------------------- groove 1,5–11 s e 11,5–13 s
chords = {1.5: 62, 3.5: 58, 5.5: 65, 7.5: 60, 9.5: 62, 11.5: 58}  # D Bb F C D Bb (baixo)
triads = {62: [62, 65, 69], 58: [58, 62, 65], 65: [65, 69, 72], 60: [60, 64, 67]}
def root_at(t): return chords[max(k for k in chords if k <= t + 1e-6)]
t = 1.5
while t < 13.0 - 1e-6:
    beat_i = round((t - 1.5) / B)
    in_break = 11.0 <= t < 11.5
    if not in_break:
        put(kick(), t, 0.95)
        if beat_i % 2 == 1: put(clap(), t, 0.42)
    hat_step = 0.125 if t >= 11.5 else 0.25
    h = 0.0
    while h < B - 1e-6:
        if h > 0 or t >= 11.5: put(hat(), t + h, 0.16, 0.6)
        h += hat_step
    if not in_break:
        r = root_at(t) - 24
        put(bass(r), t, 0.42); put(bass(r + 12, 0.2), t + 0.25, 0.32)
    t += B
# acentos
put(boom(0.7), 1.5); put(stab(triads[62], 0.5), 1.5, 0.35)
put(noise_sweep(0.35, 400, 5000), 2.2, 0.35); put(stab([62, 65, 69, 74], 0.4), 2.5, 0.35)  # entra o "E"
for i, m in enumerate([62, 65, 69, 74]): put(pluck(m + 12, 0.4, 0.75), 3.5 + i * 0.5, 0.35, 0.35 + 0.1 * i)  # morph
put(boom(0.6), 5.5); put(noise_sweep(0.7, 8000, 600, rev=True), 5.5, 0.4)  # explosão de partículas
for i in range(10): put(blip(86 + (i % 5) * 2, 0.08), 5.55 + i * 0.07, 0.12, 0.2 + 0.06 * i)  # brilhos
put(noise_sweep(1.0, 300, 7000), 6.0, 0.45)  # converge → DESIGN
put(stab([62, 65, 69, 72], 0.5), 7.0, 0.4)
put(boom(0.9), 7.5)  # cubo 3D
for i in range(4): put(clap(), 8.25 + i * 0.0625, 0.25)  # virada
put(noise_sweep(0.5, 6000, 300, rev=True), 8.5, 0.4); put(stab(triads[60], 0.35), 8.5, 0.3)
for i, at in enumerate([9.5, 9.75, 10.25, 10.6, 10.85]): put(bloop(60 + i * 3), at, 0.45, 0.3 + 0.1 * i)  # gotas
put(noise_sweep(0.6, 200, 3000), 10.95, 0.5)  # onda que inunda
for i in range(6): put(blip(79 + i * 2, 0.06), 11.5 + i * 0.1, 0.25, 0.25 + 0.1 * i)  # mosaico
put(noise_sweep(0.5, 500, 9000), 12.5, 0.45)  # colapso
# ---------------------------------------------------------------- 13 s: assinatura
put(boom(1.0), 13.0); put(pad([50, 57, 62, 65, 69, 76], 2.0), 13.0, 0.55)
for i in range(6): put(blip(88 - i, 0.05), 13.15 + i * 0.06, 0.12)
put(blip(86, 0.1), 14.75, 0.3)

# reverb curto e master
ir = rng.standard_normal((2, int(1.6 * SR))) * np.exp(-6.9 * np.arange(int(1.6 * SR)) / SR / 1.3)
ir = lp(ir, 5000); ir /= np.abs(ir).sum(axis=1, keepdims=True) ** 0.5 * 10
wet = np.stack([signal.fftconvolve(mix[c], ir[c])[:N] for c in (0, 1)])
out = hp(mix + wet * 0.5, 28)
out = np.tanh(out / (np.abs(out).max() + 1e-9) * 1.6) / np.tanh(1.6)
out *= np.minimum(1, (T - tt(N)) / 0.15)
out = out / np.abs(out).max() * 0.89
tmp = ROOT / "audio" / "_reel.wav"
sf.write(tmp, out.T.astype(np.float32), SR, subtype="FLOAT")
dst = ROOT / "public" / "reel" / "track.mp3"
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(tmp), "-t", "15", "-codec:a", "libmp3lame", "-q:a", "1", str(dst)], check=True)
tmp.unlink()
print("ok", dst)
