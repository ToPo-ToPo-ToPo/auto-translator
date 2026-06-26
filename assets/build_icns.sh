#!/usr/bin/env bash
# Render the icon and build app.icns into the .app bundle.
set -e
cd "$(dirname "$0")/.."

uv run --with pillow python assets/make_icon.py

ICONSET="$(mktemp -d)/app.iconset"
mkdir -p "$ICONSET"
SRC="assets/icon.png"

for s in 16 32 128 256 512; do
  sips -z $s $s        "$SRC" --out "$ICONSET/icon_${s}x${s}.png"        >/dev/null
  sips -z $((s*2)) $((s*2)) "$SRC" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done

iconutil -c icns "$ICONSET" -o "auto-translator.app/Contents/Resources/app.icns"
echo "wrote auto-translator.app/Contents/Resources/app.icns"
