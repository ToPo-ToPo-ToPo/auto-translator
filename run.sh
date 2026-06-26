#!/usr/bin/env bash
# Convenience launcher: uv creates/updates the venv, then runs the app.
# MLX (Gemma 4) installs automatically on Apple Silicon macOS.
# For the llama.cpp engine instead: ./run.sh --llamacpp
set -e
cd "$(dirname "$0")"

EXTRAS=()
ARGS=()
for a in "$@"; do
  case "$a" in
    --llamacpp) EXTRAS+=(--extra llamacpp) ;;
    *) ARGS+=("$a") ;;
  esac
done

uv sync "${EXTRAS[@]}"
exec uv run python app.py "${ARGS[@]}"
