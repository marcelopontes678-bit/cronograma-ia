#!/bin/sh
# Um comando: texturas → eventos → imagem → mixagem → master → legendas.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-$(cd "$HERE/../.." && pwd)}
export LIB
[ -f "$LIB/core/render/video.mjs" ] || { echo "defina LIB com a pasta da biblioteca"; exit 1; }
# navegador local, se o do Playwright não puder ser baixado
[ -n "$PLAYWRIGHT_CHROME" ] || { for c in /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell; do [ -x "$c" ] && export PLAYWRIGHT_CHROME="$c"; done; }
cd "$LIB"
.venv/bin/python -I "$HERE/tools/prep.py"
node core/render/events.mjs "$HERE" --out "$HERE/out/events.json"
node core/render/video.mjs "$HERE" --fps 24 --workers 4 --size 1080x1920 --out "$HERE/out/video.mp4"
.venv/bin/python "$HERE/mix.py"
sh "$HERE/tools/mux.sh" "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/brasil-2026.mp4" 24 1
node "$HERE/tools/cues.mjs" > "$HERE/out/cues.json"
.venv/bin/python core/render/srt.py "$HERE/out/cues.json" "$HERE/brasil-2026.srt"
