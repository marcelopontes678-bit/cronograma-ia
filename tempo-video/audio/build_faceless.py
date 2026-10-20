"""Áudio e tempos do vídeo "faceless" em português brasileiro.

Saídas:
  public/faceless/narration.wav   narração (Kokoro pm_alex, pt-BR)
  public/faceless/bed.mp3         trilha de fundo (síntese própria) — abaixa durante a fala no Remotion
  public/faceless/sfx.mp3         efeitos (whoosh, cliques, balões) — sem ducking
  src/faceless/data/timeline.json fases, legendas por grupo de palavras, marcas e duração

Uso: MODELS_DIR=/pasta/dos/modelos python audio/build_faceless.py
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
VOICE = "pm_alex"
SPEED = 1.1

# Frase = (id, texto exibido). "|" não é usado aqui: os grupos de legenda são automáticos.
PHRASES = [
    ("hook", "Veja como criar vídeos motivacionais pro TikTok e deixar a IA postar por você no piloto automático."),
    ("step1", "Primeiro, acesse faceless.video e clique em começar grátis."),
    ("step2", "Escolha vídeos motivacionais, um fundo, uma fonte, uma narração e clique em criar série."),
    ("step3", "Por fim, conecte sua conta do TikTok e a IA faz o resto: cria e posta vídeos motivacionais todo dia."),
    ("cta", "Comente IA e o link chega no seu direct."),
]
GAP = {"hook": 0.0, "step1": 0.45, "step2": 0.35, "step3": 0.35, "cta": 0.5}

# Ortografia "para falar": o TTS em pt-BR lê estrangeirismos errado.
RESPELL = {
    "faceless.video": "fêisles ponto vídeo",
    "TikTok": "tiquetóque",
    "IA": "i á",
    "direct": "dairécti",
}
HIGHLIGHT = {"ia", "tiktok", "grátis", "faceless.video", "série", "direct", "automático", "dia", "motivacionais"}


def norm(w: str) -> str:
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", w)


def strip_punct(w: str) -> str:
    return re.sub(r"[.,:;!?…]+$", "", w)


def tune(src: Path, dst: Path) -> None:
    af = ",".join(["highpass=f=80", "equalizer=f=2800:t=q:w=1.0:g=2.0", "lowshelf=f=140:g=1.5",
                   "acompressor=threshold=-18dB:ratio=3:attack=5:release=90:makeup=3"])
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-af", af, "-ar", str(SR), "-ac", "1", str(dst)], check=True)


def whisper_words(wav: Path, workdir: Path) -> list[dict]:
    workdir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["npx", "--yes", "hyperframes", "transcribe", str(wav), "--dir", str(workdir), "--model", "base",
                    "--engine", "whisper", "--language", "pt", "--json"], check=True, capture_output=True, text=True)
    return json.loads((workdir / "transcript.json").read_text())


def align(tts_tokens: list[str], heard: list[dict], dur: float) -> list[tuple[float, float]]:
    a = [norm(w) for w in tts_tokens]
    b = [norm(w["text"]) for w in heard]
    times: list[tuple[float, float] | None] = [None] * len(a)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = (heard[blk.b + k]["start"], heard[blk.b + k]["end"])
    known = [i for i, t in enumerate(times) if t]
    if not known:
        step = dur / len(a)
        return [(i * step, (i + 1) * step) for i in range(len(a))]
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
        n = j - i
        for k in range(n):
            times[i + k] = (lo + (hi - lo) * k / n, lo + (hi - lo) * (k + 1) / n)
        i = j
    return times  # type: ignore[return-value]


SHORT = {"o", "a", "e", "de", "da", "do", "no", "na", "um", "uma", "pro", "por", "com", "que", "seu", "sua", "ou", "em", "as", "os"}


def group_tokens(tokens: list[dict]) -> list[list[dict]]:
    """Agrupa palavras curtas com a seguinte (legenda gigante, 1–2 palavras por vez)."""
    groups, cur = [], []
    for t in tokens:
        cur.append(t)
        w = norm(t["w"])
        key = {norm(h) for h in HIGHLIGHT}
        if w in key:  # palavra de destaque (IA, TikTok…) fecha o grupo e aparece sozinha
            groups.append(cur)
            cur = []
            continue
        if (w in SHORT or len(w) <= 2) and len(cur) < 2 and not t["w"].endswith((",", ".", ":")):
            continue
        groups.append(cur)
        cur = []
    if cur:
        groups.append(cur)
    return groups


# ------------------------------------------------------------------- sons
def noise(n: int, rng) -> np.ndarray:
    return rng.standard_normal(n)


def bandpass(x, lo, hi, sr):
    sos = signal.butter(2, [lo, hi], btype="band", fs=sr, output="sos")
    return signal.sosfilt(sos, x)


def sfx_whoosh(sr: int, rng, dur=0.42) -> np.ndarray:
    n = int(dur * sr)
    t = np.arange(n) / sr
    x = noise(n, rng)
    out = np.zeros(n)
    seg = 512
    for i in range(0, n - seg, seg):
        fc = 350 * (4200 / 350) ** (i / n)
        out[i : i + seg] = bandpass(x[i : i + seg], fc * 0.6, min(fc * 1.5, sr / 2 - 100), sr)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
    return out * env * 0.9


def sfx_pop(sr: int, f0=720, dur=0.14) -> np.ndarray:
    t = np.arange(int(dur * sr)) / sr
    f = f0 * np.exp(-t * 9)
    return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t / 0.05)


def sfx_click(sr: int, rng) -> np.ndarray:
    n = int(0.09 * sr)
    t = np.arange(n) / sr
    c = bandpass(noise(n, rng), 1800, 7000, sr) * np.exp(-t / 0.006)
    return c * 0.8 + np.sin(2 * np.pi * 1400 * t) * np.exp(-t / 0.012) * 0.5


def sfx_ding(sr: int, dur=0.6) -> np.ndarray:
    t = np.arange(int(dur * sr)) / sr
    return (np.sin(2 * np.pi * 1318 * t) + 0.6 * np.sin(2 * np.pi * 1976 * t)) * np.exp(-t / 0.18) * 0.6


def sfx_sent(sr: int, rng, dur=0.3) -> np.ndarray:
    w = sfx_whoosh(sr, rng, dur)
    return w[::-1] * 0.5 + sfx_pop(sr, 980, dur)[: len(w)].repeat(1)[: len(w)] * 0 if False else w * 0.55


def music_bed(total: float, sr: int, rng) -> np.ndarray:
    """104 bpm, Lá menor: kick, hat, baixo e pluck. Fica discreto; o ducking é feito no Remotion."""
    n = int(total * sr)
    out = np.zeros(n)
    bpm = 104.0
    beat = 60.0 / bpm
    notes = [55.0, 43.65, 65.41, 49.0]  # A1 F1 C2 G1 (um por compasso)
    arp = [220.0, 261.63, 329.63, 392.0, 329.63, 261.63, 293.66, 329.63]
    def add(x, at, g=1.0):
        i = int(at * sr)
        if i >= n:
            return
        j = min(n, i + len(x))
        out[i:j] += x[: j - i] * g
    kick_t = np.arange(int(0.28 * sr)) / sr
    kick = np.sin(2 * np.pi * np.cumsum(48 + 90 * np.exp(-kick_t / 0.03)) / sr) * np.exp(-kick_t / 0.11)
    hat = bandpass(noise(int(0.05 * sr), rng), 6500, 10500, sr) * np.exp(-np.arange(int(0.05 * sr)) / sr / 0.012)
    snare = bandpass(noise(int(0.16 * sr), rng), 1200, 5200, sr) * np.exp(-np.arange(int(0.16 * sr)) / sr / 0.05)
    t = 0.0
    k = 0
    while t < total:
        bar = (k // 4) % 4
        if k % 4 in (0, 2):
            add(kick, t, 0.9)
        if k % 4 in (1, 3):
            add(snare, t, 0.28)
        add(hat, t, 0.22)
        add(hat, t + beat / 2, 0.14)
        # baixo
        f = notes[bar]
        bt = np.arange(int(beat * 0.95 * sr)) / sr
        b = (np.sin(2 * np.pi * f * bt) + 0.35 * np.sin(2 * np.pi * 2 * f * bt)) * np.exp(-bt / 0.45)
        if k % 4 in (0, 2, 3):
            add(b, t, 0.55)
        # pluck arpejado em colcheias
        for h in range(2):
            fa = arp[(k * 2 + h) % len(arp)]
            pt = np.arange(int(0.22 * sr)) / sr
            p = signal.sawtooth(2 * np.pi * fa * pt, 0.5) * np.exp(-pt / 0.09)
            sos = signal.butter(2, 2400, btype="low", fs=sr, output="sos")
            add(signal.sosfilt(sos, p), t + h * beat / 2, 0.16)
        t += beat
        k += 1
    sos = signal.butter(2, 9000, btype="low", fs=sr, output="sos")
    out = signal.sosfilt(sos, out)
    return out / (np.abs(out).max() + 1e-9) * 0.8


def main() -> None:
    rng = np.random.default_rng(11)
    kokoro = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
    chunks_audio: list[tuple[float, np.ndarray]] = []
    phrases_out = []
    all_tokens: list[dict] = []
    t = 0.15

    with tempfile.TemporaryDirectory() as tmp:
        tmpd = Path(tmp)
        for pid, text in PHRASES:
            t += GAP[pid]
            disp = text.split()
            tts_parts: list[list[str]] = []
            for d in disp:
                core = strip_punct(d)
                suffix = d[len(core):]
                sp = RESPELL.get(core, core).split()
                sp[-1] += suffix
                tts_parts.append(sp)
            tts_text = " ".join(" ".join(p) for p in tts_parts)
            audio, sr = kokoro.create(tts_text, voice=VOICE, speed=SPEED, lang="pt-br")
            assert sr == SR
            raw, tuned = tmpd / f"{pid}_raw.wav", tmpd / f"{pid}_t.wav"
            sf.write(raw, audio, sr)
            tune(raw, tuned)
            wav, _ = sf.read(tuned, dtype="float32")
            dur = len(wav) / SR
            chunks_audio.append((t, wav))

            flat = [w for p in tts_parts for w in p]
            heard = whisper_words(tuned, tmpd / f"w_{pid}")
            times = align(flat, heard, dur)
            idx = 0
            tokens = []
            for d, p in zip(disp, tts_parts):
                s = times[idx][0]
                e = times[idx + len(p) - 1][1]
                idx += len(p)
                tokens.append({"w": d, "s": round(t + s, 3), "e": round(t + e, 3)})
            for a, b in zip(tokens, tokens[1:]):  # sem sobreposição
                if b["s"] > a["s"]:
                    a["e"] = min(a["e"], b["s"])
            all_tokens += tokens
            phrases_out.append({"id": pid, "start": round(t, 3), "end": round(t + dur, 3), "tokens": tokens})
            print(f"{pid:6s} {t:5.2f} → {t + dur:5.2f}s")
            t += dur

    total = round(t + 0.9, 3)
    track = np.zeros(int(total * SR), dtype=np.float32)
    for at, wav in chunks_audio:
        i = int(at * SR)
        track[i : i + len(wav)] += wav
    track = track / np.abs(track).max() * 0.9
    out_dir = ROOT / "public" / "faceless"
    out_dir.mkdir(parents=True, exist_ok=True)
    sf.write(out_dir / "narration.wav", track, SR, subtype="PCM_16")

    # ---------- grupos de legenda
    caps = []
    for ph in phrases_out:
        for g in group_tokens(ph["tokens"]):
            text = " ".join(x["w"] for x in g)
            caps.append({
                "text": strip_punct(text),
                "s": g[0]["s"],
                "e": g[-1]["e"],
                "hl": any(norm(strip_punct(x["w"])) in {norm(h) for h in HIGHLIGHT} for x in g),
            })
    # cada grupo fica na tela até o próximo começar (ou 0,25 s após terminar)
    for i, c in enumerate(caps):
        nxt = caps[i + 1]["s"] if i + 1 < len(caps) else total
        c["hold"] = round(min(nxt, c["e"] + 0.3), 3)

    def find(word: str, phrase: str, nth=0, key="s"):
        ph = next(p for p in phrases_out if p["id"] == phrase)
        hits = [x for x in ph["tokens"] if norm(strip_punct(x["w"])) == norm(word)]
        return hits[nth][key]

    marks = {
        "badge": find("IA", "hook"),
        "tiktok": find("TikTok", "hook"),
        "tap1": find("grátis", "step1", key="e") - 0.12,
        "tap2": find("série", "step2", key="e") - 0.12,
        "connect": find("conecte", "step3"),
        "tiktokTile": find("TikTok", "step3"),
        "everyDay": find("dia", "step3"),
        "bubbleIA": find("IA", "cta"),
        "bubbleLink": find("link", "cta"),
        "typeUrl": find("faceless.video", "step1"),
        "voiceList": find("narração", "step2"),
        "bgList": find("fundo", "step2"),
    }
    speech = [{"start": p["start"], "end": p["end"]} for p in phrases_out]
    timeline = {
        "duration": total,
        "phrases": [{k: p[k] for k in ("id", "start", "end")} for p in phrases_out],
        "captions": caps,
        "marks": {k: round(v, 3) for k, v in marks.items()},
        "speech": speech,
    }

    # ---------- efeitos
    SRs = 44100
    sfx = np.zeros(int(total * SRs))
    def put(x, at, g=1.0):
        i = int(at * SRs)
        j = min(len(sfx), i + len(x))
        sfx[i:j] += x[: j - i] * g
    for ph in phrases_out[1:]:
        put(sfx_whoosh(SRs, rng), ph["start"] - 0.28, 0.7)
    put(sfx_pop(SRs, 640), marks["badge"], 0.8)
    put(sfx_pop(SRs, 520), marks["tiktok"], 0.5)
    put(sfx_click(SRs, rng), marks["tap1"], 0.9)
    put(sfx_whoosh(SRs, rng, 0.3), marks["bgList"] + 0.1, 0.5)
    put(sfx_whoosh(SRs, rng, 0.3), marks["voiceList"] + 0.2, 0.5)
    put(sfx_click(SRs, rng), marks["tap2"], 0.9)
    put(sfx_pop(SRs, 700), marks["tiktokTile"], 0.6)
    put(sfx_ding(SRs), marks["bubbleIA"] + 0.08, 0.75)
    put(sfx_ding(SRs), marks["bubbleLink"] + 0.1, 0.75)
    sfx = sfx / (np.abs(sfx).max() + 1e-9) * 0.85
    bed = music_bed(total, SRs, rng)
    bed[-int(0.6 * SRs):] *= np.linspace(1, 0, int(0.6 * SRs))

    for name, data in (("bed", bed), ("sfx", sfx)):
        wavp = ROOT / "audio" / f"_{name}.wav"
        sf.write(wavp, data.astype(np.float32), SRs, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wavp), "-codec:a", "libmp3lame", "-q:a", "2",
                        str(out_dir / f"{name}.mp3")], check=True)
        wavp.unlink()

    (ROOT / "src" / "faceless" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "src" / "faceless" / "data" / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1))
    print(f"ok: duração {total:.2f}s, {len(caps)} grupos de legenda")


if __name__ == "__main__":
    main()
