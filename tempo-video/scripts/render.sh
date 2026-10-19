#!/usr/bin/env bash
# Renderização resiliente: empacota uma vez, renderiza a sequência de imagens em blocos de frames
# (com nova tentativa se uma aba do Chrome travar), renderiza o áudio e junta tudo em H.264 + AAC.
#
#   bash scripts/render.sh            -> out/tempo.mp4
#   CHUNK=60 RETRIES=4 bash scripts/render.sh
#
# Pré-requisitos: node, ffmpeg. Se o Remotion não conseguir baixar o Chrome, defina
# REMOTION_BROWSER_EXECUTABLE=/caminho/chrome-headless-shell
set -euo pipefail
cd "$(dirname "$0")/.."

CHUNK="${CHUNK:-100}"
RETRIES="${RETRIES:-3}"
TOTAL=900
OUT=out
mkdir -p "$OUT/seq"

if [ ! -d "$OUT/bundle" ] || [ -n "${REBUNDLE:-}" ]; then
  npx remotion bundle src/index.ts --out-dir="$OUT/bundle" >/dev/null
fi

for ((start = 0; start < TOTAL; start += CHUNK)); do
  end=$((start + CHUNK - 1)); ((end >= TOTAL)) && end=$((TOTAL - 1))
  # já renderizado? (todos os arquivos do bloco existem, já normalizados)
  done_chunk=1
  for ((f = start; f <= end; f++)); do
    [ -f "$OUT/seq/f$(printf '%04d' "$f").jpeg" ] || { done_chunk=0; break; }
  done
  [ "$done_chunk" = 1 ] && { echo "bloco $start-$end: ok (cache)"; continue; }

  for ((try = 1; try <= RETRIES; try++)); do
    echo "bloco $start-$end (tentativa $try)"
    rm -rf "$OUT/chunk"
    if npx remotion render "$OUT/bundle" TempoVideo "$OUT/chunk" --sequence --image-format=jpeg --jpeg-quality=95 \
         --frames="$start-$end" --concurrency=3 >"$OUT/chunk.log" 2>&1; then
      # o Remotion preenche o número com a largura do bloco (00–99, 100–199…): normaliza para 4 dígitos
      for img in "$OUT"/chunk/element-*.jpeg; do
        n="${img##*element-}"; n="${n%.jpeg}"
        mv "$img" "$OUT/seq/f$(printf '%04d' "$((10#$n))").jpeg"
      done
      break
    fi
    [ "$try" = "$RETRIES" ] && { echo "falhou: bloco $start-$end"; tail -20 "$OUT/chunk.log"; exit 1; }
  done
done

echo "áudio..."
npx remotion render "$OUT/bundle" TempoVideo "$OUT/audio.wav" --codec=wav >"$OUT/audio.log" 2>&1

echo "codificando H.264 (+1,8 dB de ganho com limitador em -1 dBFS ≈ -16,6 LUFS)..."
ffmpeg -loglevel error -y -framerate 30 -i "$OUT/seq/f%04d.jpeg" -i "$OUT/audio.wav" \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -profile:v high -movflags +faststart \
  -af "volume=1.8dB,alimiter=limit=0.89:attack=5:release=60:level=disabled" \
  -c:a aac -b:a 256k -ar 48000 -t 30 "$OUT/tempo.mp4"
echo "pronto: $OUT/tempo.mp4"
