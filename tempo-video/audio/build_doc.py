"""Áudio e linha do tempo do documentário "Brasil 2026" (30 s).

Gera arquivos REAIS (nada simulado):
  public/doc/narration.wav   narração pt-BR (Kokoro pm_alex, voz adulta masculina, sintética)
  public/doc/bed.mp3         trilha de suspense sintetizada (sem amostras de terceiros)
  public/doc/sfx.mp3         efeitos: impactos graves nos cortes, carimbos, bipe da urna
  src/doc/data/timeline.json legendas (tempo por palavra), janelas de fala e marcas de tempo

Para trocar por narração humana ou trilha licenciada: substitua os arquivos em public/doc/ mantendo os
nomes (ou edite src/doc/media.ts). As legendas usam a timeline; regenere-a transcrevendo o novo áudio.

Uso: MODELS_DIR=/pasta/dos/modelos python audio/build_doc.py
"""
from __future__ import annotations

import difflib
import json
import os
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from scipy import signal

ROOT = Path(__file__).resolve().parent.parent
MODELS = Path(os.environ.get("MODELS_DIR", "/home/user/openmontage-work/models"))
SR = 24000
TOTAL = 30.0
VOICE, SPEED, PITCH = "pm_alex", 1.32, 0.95

# Texto do roteiro (literal). "|" = quebra de legenda. min_start = início mínimo (cortes de cena).
CHUNKS = [
    (1, "O Brasil se prepara | para mais uma decisão presidencial.", 0.25),
    (1, "Mas o que devemos cobrar | de quem quer governar?", 0.0),
    (2, "Escândalos políticos deixam | perguntas importantes:", 5.15),
    (2, "quem foi responsabilizado,", 0.0),
    (2, "o que dizem as decisões judiciais", 0.0),
    (2, "e quais mecanismos | podem impedir novos desvios?", 0.0),
    (3, "Conhecer os candidatos exige | examinar suas propostas, | seus históricos públicos,", 13.05),
    (3, "as evidências disponíveis | e a viabilidade | de seus compromissos.", 0.0),
    (4, "Consulte as fontes, | confira os fatos | e cobre transparência.", 21.15),
    (4, "Uma democracia exige | cidadãos bem informados.", 0.0),
]
GAP_IN_SCENE = 0.1
FINAL_TEXT_AT = 27.4  # texto final entra depois da pausa dramática

# Marcas visuais que também têm som (segundos) — o vídeo lê estes mesmos valores.
MARKS = {
    "cut2": 5.0, "cut3": 13.0, "cut4": 21.0,
    "card1": 7.4, "stamp1": 8.1, "card2": 8.8, "stamp2": 9.5,
    "legend": [10.2, 10.65, 11.1, 11.55, 12.0],
    "stamp3": 17.4,
    "confirm": 25.7,
    "finalText": FINAL_TEXT_AT,
}


def norm(w: str) -> str:
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", w)


def tune(src: Path, dst: Path) -> None:
    """Tom levemente mais grave, presença, compressão e corte de silêncio no início/fim."""
    af = ",".join([
        f"rubberband=pitch={PITCH}", "highpass=f=70", "lowshelf=f=160:g=2.5",
        "equalizer=f=3000:t=q:w=1.0:g=1.5", "acompressor=threshold=-20dB:ratio=3:attack=6:release=100:makeup=3",
        "silenceremove=start_periods=1:start_threshold=-42dB",
        "areverse", "silenceremove=start_periods=1:start_threshold=-42dB", "areverse",
    ])
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-af", af, "-ar", str(SR), "-ac", "1", str(dst)], check=True)


def whisper_words(wav: Path, workdir: Path) -> list[dict]:
    workdir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["npx", "--yes", "hyperframes", "transcribe", str(wav), "--dir", str(workdir), "--model", "base",
                    "--engine", "whisper", "--language", "pt", "--json"], check=True, capture_output=True, text=True)
    return json.loads((workdir / "transcript.json").read_text())


def align(words: list[str], heard: list[dict], dur: float) -> list[tuple[float, float]]:
    a = [norm(w) for w in words]
    b = [norm(h["text"]) for h in heard]
    times: list = [None] * len(a)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = (heard[blk.b + k]["start"], heard[blk.b + k]["end"])
    i = 0
    while i < len(a):
        if times[i]:
            i += 1
            continue
        j = i
        while j < len(a) and not times[j]:
            j += 1
        lo = times[i - 1][1] if i > 0 else 0.0
        hi = times[j][0] if j < len(a) else dur
        for k in range(j - i):
            times[i + k] = (lo + (hi - lo) * k / (j - i), lo + (hi - lo) * (k + 1) / (j - i))
        i = j
    return times


# ------------------------------------------------------------------ trilha
SRM = 44100
rng = np.random.default_rng(2026)


def tt(n): return np.arange(n) / SRM
def lp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, "low", fs=SRM, output="sos"), x, axis=-1)
def hp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, "high", fs=SRM, output="sos"), x, axis=-1)
def bp(x, a, b): return signal.sosfilt(signal.butter(2, [a, b], "band", fs=SRM, output="sos"), x)
def hz(m): return 440 * 2 ** ((m - 69) / 12)


def curve(pts, n):
    xs, ys = zip(*pts)
    return np.interp(tt(n), xs, ys)


def boom(g=1.0):
    t = tt(int(1.6 * SRM)); f = 34 + 55 * np.exp(-t / 0.08)
    return (np.sin(2 * np.pi * np.cumsum(f) / SRM) * np.exp(-t / 0.6) + lp(rng.standard_normal(len(t)), 700) * np.exp(-t / 0.06) * 0.4) * g


def build_music() -> tuple[np.ndarray, np.ndarray]:
    N = int(TOTAL * SRM)
    t = tt(N)
    bed = np.zeros((2, N))
    # drone grave (Ré) que cresce
    drone = sum(g * np.sin(2 * np.pi * f * t + ph) for f, g, ph in ((36.7, 1.0, 0), (55.0, 0.5, 1), (73.4, 0.35, 2)))
    drone += lp(rng.standard_normal(N), 120) * 0.6
    drone *= curve([(0, 0.25), (5, 0.4), (13, 0.55), (21, 0.7), (26.6, 0.95), (26.85, 0.0), (30, 0.0)], N)
    bed += np.stack([drone, np.roll(drone, 40)]) * 0.35
    # tique de relógio sutil (tensão)
    for k in range(0, 27):
        n = int(0.05 * SRM)
        tick = hp(rng.standard_normal(n), 3000) * np.exp(-tt(n) / 0.004)
        i = int((k + 0.02) * SRM)
        bed[:, i:i + n] += tick * (0.09 if k < 21 else 0.12)
    # ostinato staccato (cordas sintéticas) a partir do corte 2, cada vez mais presente
    notes = [62, 65, 69, 65, 62, 65, 70, 69]
    step = 0.3
    t0 = 5.0
    k = 0
    while t0 < 26.7:
        m = notes[k % len(notes)] - (12 if t0 < 13 else 0)
        n = int(0.22 * SRM)
        tn = tt(n)
        x = sum(signal.sawtooth(2 * np.pi * hz(m) * (1 + d) * tn) for d in (-0.004, 0.004)) * np.exp(-tn / 0.07)
        x = lp(x, 1400 + 120 * (t0 - 5))
        g = np.interp(t0, [5, 13, 21, 26.6], [0.05, 0.09, 0.13, 0.18])
        i = int(t0 * SRM)
        bed[0, i:i + n] += x * g * (0.6 if k % 2 else 1.0)
        bed[1, i:i + n] += x * g * (1.0 if k % 2 else 0.6)
        t0 += step
        k += 1
    # pad sombrio a partir de 13 s
    pad = sum(signal.sawtooth(2 * np.pi * hz(m) * (1 + d) * t, 0.5) for m in (50, 57, 62, 65) for d in (-0.003, 0.003))
    pad = lp(pad, 900) * curve([(0, 0), (13, 0), (16, 0.05), (21, 0.08), (26.6, 0.12), (26.85, 0), (30, 0)], N)
    bed += np.stack([pad, np.roll(pad, 25)]) * 0.5
    # acorde final depois da pausa dramática
    n = int((TOTAL - FINAL_TEXT_AT) * SRM)
    tn = tt(n)
    fin = sum(np.sin(2 * np.pi * hz(m) * tn) * g for m, g in ((38, 1.0), (50, 0.6), (57, 0.45), (62, 0.4), (65, 0.3), (69, 0.25)))
    fin *= np.minimum(1, tn / 0.03) * np.exp(-tn / 1.6) * 0.32
    i = int(FINAL_TEXT_AT * SRM)
    bed[:, i:i + n] += fin

    # reverb
    ir = rng.standard_normal((2, int(2.4 * SRM))) * np.exp(-6.9 * tt(int(2.4 * SRM)) / 2.0)
    ir = lp(ir, 4500); ir /= np.abs(ir).sum(axis=1, keepdims=True) ** 0.5 * 9
    bed = bed + np.stack([signal.fftconvolve(bed[c], ir[c])[:N] for c in (0, 1)]) * 0.6
    bed = hp(bed, 25)
    bed *= np.minimum(1, (TOTAL - t) / 0.3)
    bed = bed / np.abs(bed).max() * 0.85

    # efeitos (sem ducking)
    sfx = np.zeros((2, N))
    def put(x, at, g=1.0):
        i = int(at * SRM); j = min(N, i + len(x))
        sfx[:, i:j] += x[: j - i] * g
    for c in ("cut2", "cut3", "cut4"):
        put(boom(0.9), MARKS[c])
    def stamp():
        n = int(0.25 * SRM); tn = tt(n)
        return lp(rng.standard_normal(n), 600) * np.exp(-tn / 0.03) + np.sin(2 * np.pi * 70 * tn) * np.exp(-tn / 0.08) * 0.8
    def paper():
        n = int(0.3 * SRM); tn = tt(n)
        return bp(rng.standard_normal(n), 1500, 7000) * np.sin(np.pi * tn / tn[-1]) ** 2 * 0.5
    for s in ("stamp1", "stamp2", "stamp3"):
        put(stamp(), MARKS[s], 0.8)
    for s in ("card1", "card2"):
        put(paper(), MARKS[s] - 0.1, 0.6)
    for t_ in MARKS["legend"]:
        n = int(0.06 * SRM); put(np.sin(2 * np.pi * 1800 * tt(n)) * np.exp(-tt(n) / 0.015), t_, 0.25)
    # bipe de confirmação (urna)
    n = int(0.11 * SRM); beep = np.sign(np.sin(2 * np.pi * 1550 * tt(n))) * 0.2
    for k in range(4):
        put(beep, MARKS["confirm"] + k * 0.13, 0.5)
    n = int(0.5 * SRM); put(np.sign(np.sin(2 * np.pi * 1550 * tt(n))) * 0.2 * np.minimum(1, (0.5 - tt(n)) / 0.05), MARKS["confirm"] + 0.52, 0.5)
    put(boom(1.0), FINAL_TEXT_AT)
    sfx = lp(sfx, 9000)
    sfx = sfx / np.abs(sfx).max() * 0.8
    return bed, sfx


def main() -> None:
    kokoro = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
    track = np.zeros(int(TOTAL * SR), dtype=np.float32)
    pages, speech, phrases = [], [], []
    t = 0.0
    prev_scene = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmpd = Path(tmp)
        for i, (scene, text, min_start) in enumerate(CHUNKS):
            start = max(t + (GAP_IN_SCENE if scene == prev_scene else 0.2), min_start)
            prev_scene = scene
            spoken = text.replace("|", "").replace("  ", " ")
            audio, sr = kokoro.create(spoken, voice=VOICE, speed=SPEED, lang="pt-br")
            raw, tuned = tmpd / f"r{i}.wav", tmpd / f"t{i}.wav"
            sf.write(raw, audio, sr)
            tune(raw, tuned)
            wav, _ = sf.read(tuned, dtype="float32")
            dur = len(wav) / SR
            a = int(start * SR)
            assert a + len(wav) <= len(track), f"frase {i} passa de 30 s"
            track[a:a + len(wav)] += wav
            words, breaks = [], set()
            for tok in text.split():
                if tok == "|":
                    breaks.add(len(words))
                else:
                    words.append(tok)
            heard = whisper_words(tuned, tmpd / f"w{i}")
            times = align(words, heard, dur)
            wl = [{"w": w, "s": round(start + s, 3), "e": round(start + e, 3)} for w, (s, e) in zip(words, times)]
            for x, y in zip(wl, wl[1:]):
                if y["s"] > x["s"]:
                    x["e"] = min(x["e"], y["s"])
            cuts = [0, *sorted(breaks), len(wl)]
            for p, q in zip(cuts, cuts[1:]):
                pg = wl[p:q]
                pages.append({"start": pg[0]["s"], "end": pg[-1]["e"], "scene": scene, "words": pg})
            speech.append({"start": round(start, 3), "end": round(start + dur, 3)})
            phrases.append({"scene": scene, "start": round(start, 3), "end": round(start + dur, 3), "text": spoken})
            print(f"cena {scene}  {start:5.2f} → {start + dur:5.2f}s  {spoken}")
            t = start + dur
    assert t < FINAL_TEXT_AT - 0.5, f"narração termina em {t:.2f}s: sem espaço para a pausa dramática"
    track = track / np.abs(track).max() * 0.9
    out = ROOT / "public" / "doc"
    out.mkdir(parents=True, exist_ok=True)
    sf.write(out / "narration.wav", track, SR, subtype="PCM_16")

    bed, sfx = build_music()
    for name, data in (("bed", bed), ("sfx", sfx)):
        wavp = ROOT / "audio" / f"_doc_{name}.wav"
        sf.write(wavp, data.T.astype(np.float32), SRM, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wavp), "-t", "30", "-codec:a", "libmp3lame", "-q:a", "1", str(out / f"{name}.mp3")], check=True)
        wavp.unlink()

    data = ROOT / "src" / "doc" / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "timeline.json").write_text(json.dumps({"pages": pages, "speech": speech, "phrases": phrases, "marks": MARKS}, ensure_ascii=False, indent=1))
    print(f"ok: narração termina em {t:.2f}s; pausa até {FINAL_TEXT_AT}s; {len(pages)} legendas")


if __name__ == "__main__":
    main()
