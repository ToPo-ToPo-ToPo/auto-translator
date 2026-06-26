#!/usr/bin/env bash
# Convenience launcher: uv creates/updates the venv, then runs the app.
# Optional LLM engines: ./run.sh --mlx   or   ./run.sh --llamacpp
set -e
cd "$(dirname "$0")"

EXTRAS=()
ARGS=()
for a in "$@"; do
  case "$a" in
    --mlx) EXTRAS+=(--extra mlx) ;;
    --llamacpp) EXTRAS+=(--extra llamacpp) ;;
    *) ARGS+=("$a") ;;
  esac
done

uv sync "${EXTRAS[@]}"
exec uv run python app.py "${ARGS[@]}"
