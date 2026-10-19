"""Sintetiza a trilha (30 s, estéreo 44,1 kHz) sem nenhuma amostra externa.

Linha do tempo (segue a direção de som do briefing):
  0–8 s    só o relógio (tique a cada segundo, no mesmo instante em que o ponteiro "bate" no vídeo)
  8 s →    camadas entram aos poucos: drone grave, pad em Lá menor, piano grave
  12 s →   arpejo de piano e pulsação (coração/relógio, 60 bpm)
  21–27 s  clímax: riser, oitavas no piano, pad aberto, pulsação forte
  27.0 s   impacto grave + nota de piano sustentada (Lá), decaimento natural até o fim

Uso: python audio/build_music.py   (precisa de numpy, scipy, soundfile, ffmpeg)
Saída: public/audio/music.mp3
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

ROOT = Path(__file__).resolve().parent.parent
SR = 44100
T = 30.0
N = int(T * SR)
rng = np.random.default_rng(7)  # determinístico


def tt(n: int) -> np.ndarray:
    return np.arange(n) / SR


def add(buf: np.ndarray, x: np.ndarray, start: float, gain: float = 1.0) -> None:
    i = int(start * SR)
    if i >= buf.shape[-1]:
        return
    j = min(buf.shape[-1], i + x.shape[-1])
    buf[..., i:j] += x[..., : j - i] * gain


def ramp(t: float, points: list[tuple[float, float]]) -> float:
    xs, ys = zip(*points)
    return float(np.interp(t, xs, ys))


def curve(points: list[tuple[float, float]]) -> np.ndarray:
    xs, ys = zip(*points)
    return np.interp(tt(N), xs, ys)


def lowpass(x: np.ndarray, fc: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, fc, btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=-1)


def highpass(x: np.ndarray, fc: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, fc, btype="high", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=-1)


def hz(note: str) -> float:
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    n = names[note[0]]
    acc = 1 if "#" in note else 0
    octave = int(note[-1])
    midi = 12 * (octave + 1) + n + acc
    return 440.0 * 2 ** ((midi - 69) / 12)


# --------------------------------------------------------------------------- relógio
def tick(pitch: float = 1.0) -> np.ndarray:
    n = int(0.12 * SR)
    t = tt(n)
    click = highpass(rng.standard_normal(n), 2500) * np.exp(-t / 0.0018)
    body = np.sin(2 * np.pi * 1750 * pitch * t) * np.exp(-t / 0.006) * 0.55
    thunk = np.sin(2 * np.pi * 210 * pitch * t) * np.exp(-t / 0.022) * 0.45
    x = click * 0.9 + body + thunk
    return x / np.abs(x).max()


def clock_layer() -> np.ndarray:
    out = np.zeros((2, N))
    for k in range(0, 30):
        # forte nos 8 s iniciais ("som isolado"), depois recua; some antes da pulsação dominar
        g = ramp(k, [(0, 0.95), (7, 0.95), (10, 0.42), (18, 0.22), (20, 0.0)])
        if g <= 0.001:
            continue
        x = tick(1.0 if k % 2 == 0 else 0.86)
        pan = 0.46 + 0.08 * (k % 2)
        add(out[0], x, k, g * (1 - pan))
        add(out[1], x, k, g * pan)
    return out


# --------------------------------------------------------------------------- piano
def piano(f: float, vel: float = 0.7, dur: float = 6.5) -> np.ndarray:
    n = int(dur * SR)
    t = tt(n)
    out = np.zeros(n)
    t0 = 4.2 * (110.0 / f) ** 0.32  # notas graves soam mais
    b = 0.00035 * (f / 220.0) ** 1.4  # inarmonicidade das cordas
    bright = (1.0 - vel) * 0.42
    for detune in (-0.55, 0.0, 0.55):  # 3 cordas levemente desafinadas
        for k in range(1, 15):
            fk = f * k * np.sqrt(1 + b * k * k) + detune * (1 + 0.15 * k)
            if fk > 9000:
                break
            a = (1.0 / k**1.08) * np.exp(-k * bright)
            tau = t0 / (1 + 0.5 * (k - 1))
            env = 0.62 * np.exp(-t / tau) + 0.38 * np.exp(-t / (tau * 4.0))
            out += a * env * np.sin(2 * np.pi * fk * t + k * 0.7)
    attack = 1 - np.exp(-t / 0.0022)
    out *= attack
    hn = int(0.012 * SR)
    hammer = lowpass(rng.standard_normal(hn), 2500) * np.exp(-tt(hn) / 0.003)
    out[:hn] += hammer * 0.35 * vel
    out /= np.abs(out).max()
    return out * (0.35 + 0.65 * vel)


# --------------------------------------------------------------------------- pad
def pad_voice(f: float, length: float, att: float, rel: float, bright: np.ndarray, side: int) -> np.ndarray:
    n = int(length * SR)
    t = tt(n)
    out = np.zeros(n)
    for dt in (-0.9, 0.0, 0.9):
        phase = rng.uniform(0, 2 * np.pi)
        for k in range(1, 16):
            fk = f * k * (1 + (dt + 0.4 * side) * 0.0009)
            if fk > 7000:
                break
            kmax = bright[:n] if bright.shape[0] >= n else np.pad(bright, (0, n - bright.shape[0]), mode="edge")
            out += (1.0 / k) * np.exp(-k / kmax) * np.sin(2 * np.pi * fk * t + phase * k)
    env = np.minimum(1, t / att) * np.minimum(1, (length - t) / rel)
    return out * env


def pad_layer() -> np.ndarray:
    out = np.zeros((2, N))
    bars = [  # (início, acorde)
        (8, ["A2", "E3", "A3", "C4"]),
        (12, ["F2", "C3", "A3", "F4"]),
        (16, ["C3", "G3", "E4", "C4"]),
        (20, ["G2", "D3", "B3", "G4"]),
        (24, ["A2", "E3", "A3", "C4", "E4"]),
    ]
    for start, chord in bars:
        length = 4.0 + 1.6 + 1.2
        # o timbre abre (mais harmônicos) conforme o vídeo avança
        bright_t = start + tt(int(length * SR))
        bright = np.interp(bright_t, [8, 20, 26], [3.5, 7.0, 13.0])
        for i, note in enumerate(chord):
            for side, ch in ((-1, 0), (1, 1)):
                v = pad_voice(hz(note), length, 1.6, 1.8, bright, side)
                add(out[ch], v, start - 1.2, 0.045)
    env = curve([(0, 0), (8, 0), (11, 0.30), (20, 0.50), (22.5, 0.80), (26.9, 1.0), (27.4, 0.0), (30, 0)])
    return out * env


def drone_layer() -> np.ndarray:
    t = tt(N)
    d = (np.sin(2 * np.pi * 55 * t) * 0.8 + np.sin(2 * np.pi * 110 * t + 0.4) * 0.28
         + np.sin(2 * np.pi * 82.4 * t) * 0.22)
    d += lowpass(rng.standard_normal(N), 180) * 0.25  # ar/ambiente
    env = curve([(0, 0), (7.6, 0), (12, 0.30), (21, 0.50), (26.95, 1.0), (27.6, 0.0)])
    mod = 1 + 0.06 * np.sin(2 * np.pi * 0.11 * t)
    x = d * env * mod * 0.34
    return np.stack([x, np.roll(x, 7)])


# --------------------------------------------------------------------------- pulsação
def thump(strength: float) -> np.ndarray:
    n = int(0.55 * SR)
    t = tt(n)
    f = 46 + 70 * np.exp(-t / 0.045)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / 0.16)
    x += lowpass(rng.standard_normal(n), 400) * np.exp(-t / 0.012) * 0.25
    return x / np.abs(x).max() * strength


def pulse_layer() -> np.ndarray:
    out = np.zeros((2, N))
    for k in range(12, 27):
        g = ramp(k, [(12, 0.05), (18, 0.16), (22, 0.45), (26, 0.75)])
        lub = thump(g)
        dub = thump(g * 0.55)
        for ch in (0, 1):
            add(out[ch], lub, k, 1.0)
            add(out[ch], dub, k + 0.30, 1.0)
    return out


# --------------------------------------------------------------------------- piano: partitura
CHORD_TONES = {
    8: ["A3", "C4", "E4", "A4"],
    12: ["F3", "A3", "C4", "F4"],
    16: ["C4", "E4", "G4", "C5"],
    20: ["G3", "B3", "D4", "G4"],
    24: ["A3", "C4", "E4", "A4"],
}
BASS = {8: "A2", 12: "F2", 16: "C3", 20: "G2", 24: "A2"}


def piano_layer() -> np.ndarray:
    mono = np.zeros(N)
    for bar, bass in BASS.items():
        # mão esquerda: nota grave no início do compasso (entra a partir dos 8 s)
        add(mono, piano(hz(bass), 0.50 if bar < 16 else 0.7, 7.0), bar + 0.02, 0.7 if bar < 16 else 0.95)
        if bar >= 16:
            add(mono, piano(hz(bass) * 2, 0.55, 5.0), bar + 2.0, 0.5)
    # mão direita: arpejo lento (1 nota/s) a partir de 12 s; dobra a velocidade no clímax
    pattern = [0, 2, 1, 3, 2, 1, 3, 2]
    t = 12.0
    idx = 0
    while t < 26.9:
        bar = max(b for b in CHORD_TONES if b <= t)
        tones = CHORD_TONES[bar]
        step = 1.0 if t < 20.5 else 0.5
        vel = ramp(t, [(12, 0.30), (20, 0.48), (24, 0.85), (26.9, 0.95)])
        note = tones[pattern[idx % len(pattern)]]
        add(mono, piano(hz(note), vel, 4.5), t, 0.55)
        if t >= 22.0 and idx % 2 == 0:  # oitava acima no clímax
            add(mono, piano(hz(note) * 2, vel * 0.8, 3.5), t + 0.01, 0.30)
        t += step
        idx += 1
    # frase de abertura (antes da pulsação): duas notas isoladas
    add(mono, piano(hz("A3"), 0.40, 6.0), 9.5, 0.5)
    add(mono, piano(hz("E4"), 0.38, 6.0), 10.5, 0.45)
    return np.stack([mono, np.roll(mono, 11)])  # leve abertura estéreo


def final_note() -> np.ndarray:
    out = np.zeros((2, N))
    # impacto grave + nota sustentada
    boom = thump(1.0)
    n = int(3.2 * SR)
    t = tt(n)
    sub = np.sin(2 * np.pi * 41 * t) * np.exp(-t / 0.9) * 0.9
    for ch in (0, 1):
        add(out[ch], boom, 27.0, 0.9)
        add(out[ch], sub, 27.0, 0.55)
    p = piano(hz("A3"), 0.88, 3.4) * 0.85 + piano(hz("A2"), 0.8, 3.4) * 0.6
    p = np.stack([p, np.roll(p, 9)])
    for ch in (0, 1):
        add(out[ch], p[ch], 27.02, 1.0)
    return out


def riser_layer() -> np.ndarray:
    n = N
    noise = rng.standard_normal(n)
    # varredura de filtro: centro 250 Hz → 5 kHz entre 20,5 e 27 s
    out = np.zeros(n)
    seg = int(0.25 * SR)
    for i in range(0, n - seg, seg):
        tc = (i + seg / 2) / SR
        if tc < 20.5 or tc > 27.2:
            continue
        fc = 250 * (5000 / 250) ** ((tc - 20.5) / 6.5)
        sos = signal.butter(2, [fc * 0.7, fc * 1.4], btype="band", fs=SR, output="sos")
        out[i : i + seg] = signal.sosfilt(sos, noise[i : i + seg])
    env = curve([(0, 0), (20.5, 0), (24, 0.25), (26.6, 1.0), (26.98, 0.9), (27.05, 0.0)]) ** 1.6
    x = out * env * 0.9
    return np.stack([x, np.roll(x, 53)])


# --------------------------------------------------------------------------- reverb
def reverb_ir(rt60: float = 3.2) -> np.ndarray:
    n = int(rt60 * 1.25 * SR)
    t = tt(n)
    ir = np.stack([rng.standard_normal(n), rng.standard_normal(n)])
    ir *= np.exp(-6.9 * t / rt60)
    ir = lowpass(ir, 5200)
    ir[:, : int(0.025 * SR)] = 0  # pré-atraso
    ir /= np.abs(ir).sum(axis=1, keepdims=True) ** 0.5 * 8
    return ir


def reverb(x: np.ndarray, ir: np.ndarray) -> np.ndarray:
    wet = np.stack([signal.fftconvolve(x[c], ir[c])[:N] for c in range(2)])
    return wet


# --------------------------------------------------------------------------- mix
def main() -> None:
    ir = reverb_ir()
    clock = clock_layer()
    drone = drone_layer()
    pad = pad_layer()
    piano_l = piano_layer()
    pulse = pulse_layer()
    riser = riser_layer()
    final = final_note()

    # piano/pad/final passam pela sala; relógio e pulsação ficam secos (mais "isolados")
    wet_src = piano_l * 0.9 + pad * 1.0 + final * 0.9
    wet = reverb(wet_src, ir)
    mix = (
        clock * 0.95
        + drone * 0.9
        + pulse * 0.62
        + riser * 0.16
        + piano_l * 0.55
        + pad * 0.85
        + final * 0.8
        + wet * 1.3
    )

    mix = highpass(mix, 28)
    mix = lowpass(mix, 15500, order=1)
    # remove o resto do reverb depois do fim sem cortar seco: fade curtíssimo
    fade = int(0.35 * SR)
    mix[:, -fade:] *= np.linspace(1, 0, fade)
    mix[:, :64] *= np.linspace(0, 1, 64)
    peak = np.abs(mix).max()
    mix = mix / peak * 0.80  # ≈ -2 dBFS; o Remotion ajusta o volume final

    wav = ROOT / "audio" / "_music_tmp.wav"
    sf.write(wav, mix.T.astype(np.float32), SR, subtype="FLOAT")
    out = ROOT / "public" / "audio" / "music.mp3"
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-t", "30",
                    "-codec:a", "libmp3lame", "-q:a", "1", str(out)], check=True)
    wav.unlink()
    print("ok →", out, f"{out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
