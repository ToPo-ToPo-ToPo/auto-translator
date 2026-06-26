#!/usr/bin/env bash
# Convenience launcher: sets up a local venv on first run, then starts the app.
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment (.venv)…"
  python3 -m venv .venv
  ./.venv/bin/pip install --upgrade pip >/dev/null
  ./.venv/bin/pip install -r requirements.txt
fi

exec ./.venv/bin/python app.py "$@"
