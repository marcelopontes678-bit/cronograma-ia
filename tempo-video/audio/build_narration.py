"""Gera a narração (Kokoro, pt-BR, voz masculina) e as legendas sincronizadas.

Saídas:
  public/audio/narration.wav     trilha de 30 s, mono, 24 kHz, com cada frase na posição certa
  src/data/captions.json         páginas de legenda com tempo por palavra (Whisper + roteiro)
  src/data/speech.json           janelas de fala (usadas para baixar a música durante a voz)

Uso:
  MODELS_DIR=/caminho/dos/modelos python audio/build_narration.py

MODELS_DIR precisa conter kokoro-v1.0.onnx e voices-v1.0.bin.
A transcrição usa `npx hyperframes transcribe` (whisper.cpp, modelo `base`, --language pt).
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

ROOT = Path(__file__).resolve().parent.parent
MODELS = Path(os.environ.get("MODELS_DIR", "/home/user/openmontage-work/models"))
SR = 24000
TOTAL = 30.0
VOICE = "pm_alex"
PITCH = 0.93  # < 1 = mais grave (rubberband, mantém a duração)

# Cada frase: texto, início absoluto (s) e pausa antes dela (já embutida no início).
# `gain` cresce ao longo do vídeo (intensidade crescente).
CHUNKS = [
    # cena 1
    dict(text="O tempo está passando.", start=0.45, speed=0.95, gain=0.80),
    dict(text="Mesmo quando você não faz nada.", start=2.55, speed=0.95, gain=0.80),
    # cena 2
    dict(text="Cada dia que você desperdiça | é um pedaço da sua vida | que não volta.", start=5.45, speed=0.92, gain=0.86),
    # cena 3
    dict(text="Você pode continuar adiando | o que precisa fazer", start=11.30, speed=1.0, gain=0.92),
    dict(text="ou começar a construir | aquilo que deseja ser.", start=15.05, speed=1.0, gain=0.96),
    # cena 4
    dict(text="Não espere sentir vontade.", start=18.45, speed=1.0, gain=1.00),
    dict(text="Discipline seus passos.", start=21.00, speed=1.0, gain=1.02),
    dict(text="Honre o tempo que ainda tem.", start=23.00, speed=1.0, gain=1.04),
    # cena 5
    dict(text="Porque, no fim, | sua vida será a soma | daquilo que decidiu | fazer com o tempo.", start=25.05, speed=1.0, gain=1.06),
]


def norm(word: str) -> str:
    w = unicodedata.normalize("NFD", word.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", w)


def tune(wav_in: Path, wav_out: Path) -> None:
    """Voz mais grave, íntima e sem sibilância dura: pitch↓, low-shelf, compressão, sala curta."""
    af = ",".join([
        f"rubberband=pitch={PITCH}",
        "highpass=f=70",
        "lowshelf=f=180:g=3.5",
        "equalizer=f=3200:t=q:w=1.2:g=-2.0",
        "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2",
        "aecho=0.88:0.5:48|83:0.14|0.08",
    ])
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav_in), "-af", af,
                    "-ar", str(SR), "-ac", "1", str(wav_out)], check=True)


def whisper_words(wav: Path, workdir: Path) -> list[dict]:
    """Palavras com tempo (s, relativo ao arquivo) via hyperframes/whisper.cpp."""
    workdir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["npx", "--yes", "hyperframes", "transcribe", str(wav), "--dir", str(workdir),
         "--model", "base", "--engine", "whisper", "--language", "pt", "--json"],
        check=True, capture_output=True, text=True,
    )
    return json.loads((workdir / "transcript.json").read_text())


def align(script_words: list[str], heard: list[dict], dur: float) -> list[tuple[float, float]]:
    """Mapeia as palavras do roteiro (texto correto) nos tempos do Whisper."""
    a = [norm(w) for w in script_words]
    b = [norm(w["text"]) for w in heard]
    times: list[tuple[float, float] | None] = [None] * len(a)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            h = heard[blk.b + k]
            times[blk.a + k] = (h["start"], h["end"])
    # palavras sem par: interpola entre vizinhas conhecidas
    known = [i for i, t in enumerate(times) if t]
    if not known:
        step = dur / len(a)
        return [(i * step, (i + 1) * step) for i in range(len(a))]
    for i in range(len(a)):
        if times[i]:
            continue
        left = max((j for j in known if j < i), default=None)
        right = min((j for j in known if j > i), default=None)
        lo = times[left][1] if left is not None else 0.0
        hi = times[right][0] if right is not None else dur
        gap = [j for j in range(len(a)) if times[j] is None and (left or -1) < j < (right if right is not None else len(a))]
        n = len(gap)
        idx = gap.index(i)
        s = lo + (hi - lo) * idx / n
        e = lo + (hi - lo) * (idx + 1) / n
        times[i] = (s, e)
    return times  # type: ignore[return-value]


STOP = {"o", "a", "os", "as", "um", "uma", "de", "da", "do", "das", "dos", "que", "e", "com",
        "é", "no", "na", "nos", "nas", "ou", "para", "em", "por", "se", "não", "sua", "seu"}


def pages_for(words: list[dict], max_words: int = 5, max_chars: int = 32) -> list[list[dict]]:
    """Agrupa palavras em páginas curtas (≤ 5 palavras), sem terminar em artigo/preposição."""
    pages, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        chars = sum(len(x["w"]) + 1 for x in cur)
        clause = w["w"].endswith((".", ",", ";", ":", "…", "?", "!"))
        full = len(cur) >= max_words or chars >= max_chars
        last = i == len(words) - 1
        dangling = norm(w["w"]) in STOP and not clause
        if last:
            break
        if (clause and len(cur) >= 2) or (full and not dangling) or len(cur) >= max_words + 2:
            pages.append(cur)
            cur = []
    if cur:
        if pages and len(cur) <= 2 and len(pages[-1]) + len(cur) <= max_words + 2:
            pages[-1].extend(cur)
        else:
            pages.append(cur)
    return pages


def main() -> None:
    kokoro = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
    track = np.zeros(int(TOTAL * SR), dtype=np.float32)
    all_pages: list[dict] = []
    speech: list[dict] = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for i, ch in enumerate(CHUNKS):
            raw = tmp_dir / f"raw{i}.wav"
            tuned = tmp_dir / f"tuned{i}.wav"
            audio, sr = kokoro.create(ch["text"].replace("|", ""), voice=VOICE, speed=ch["speed"], lang="pt-br")
            assert sr == SR, sr
            sf.write(raw, audio, sr)
            tune(raw, tuned)
            wav, _ = sf.read(tuned, dtype="float32")
            wav = wav * ch["gain"]
            s0 = int(ch["start"] * SR)
            end = s0 + len(wav)
            assert end <= len(track), f"frase {i} passa de {TOTAL}s"
            track[s0:end] += wav
            dur = len(wav) / SR
            print(f"[{i}] {ch['start']:5.2f}s → {ch['start'] + dur:5.2f}s  {ch['text'][:48]}")

            heard = whisper_words(tuned, tmp_dir / f"w{i}")
            # "|" no texto marca quebra de página da legenda (não é falado)
            words, breaks = [], set()
            for tok in ch["text"].split():
                if tok == "|":
                    breaks.add(len(words))
                else:
                    words.append(tok)
            times = align(words, heard, dur)
            first = min(t[0] for t in times)
            last = max(t[1] for t in times)
            speech.append({"start": round(ch["start"] + first, 3), "end": round(ch["start"] + last, 3)})
            wlist = [
                {"w": w, "s": round(ch["start"] + t[0], 3), "e": round(ch["start"] + t[1], 3)}
                for w, t in zip(words, times)
            ]
            # nenhuma palavra termina depois da próxima começar
            for a, b in zip(wlist, wlist[1:]):
                a["e"] = min(a["e"], b["s"]) if b["s"] > a["s"] else a["e"]
            if breaks:
                cuts = [0, *sorted(breaks), len(wlist)]
                chunk_pages = [wlist[a:b] for a, b in zip(cuts, cuts[1:])]
            else:
                chunk_pages = pages_for(wlist)
            for pg in chunk_pages:
                all_pages.append({
                    "start": pg[0]["s"],
                    "end": round(pg[-1]["e"], 3),
                    "words": pg,
                })

    peak = float(np.abs(track).max())
    track = track / peak * 0.89  # ~ -1 dBFS
    out = ROOT / "public" / "audio" / "narration.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, track, SR, subtype="PCM_16")

    data = ROOT / "src" / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "captions.json").write_text(json.dumps(all_pages, ensure_ascii=False, indent=1))
    (data / "speech.json").write_text(json.dumps(speech, indent=1))
    print(f"ok: {len(all_pages)} páginas de legenda, narração {len(track) / SR:.2f}s → {out}")


if __name__ == "__main__":
    main()
