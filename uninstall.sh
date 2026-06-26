#!/usr/bin/env bash
# Uninstall auto-translator's local data. Safe by default: only removes things
# this app created. The project folder itself is left in place (delete it
# yourself afterwards if you want).
#
# Usage:
#   ./uninstall.sh           # venv, logs, caches, Argos language models
#   ./uninstall.sh --keep-models   # keep downloaded Argos language models
#   ./uninstall.sh --all     # also remove downloaded Gemma 4 LLM models (HF cache)
#   ./uninstall.sh --yes     # don't ask for confirmation
set -e
cd "$(dirname "$0")"
PROJECT="$(pwd)"

KEEP_MODELS=0; REMOVE_LLM=0; ASSUME_YES=0
for a in "$@"; do
  case "$a" in
    --keep-models) KEEP_MODELS=1 ;;
    --all)         REMOVE_LLM=1 ;;
    --yes|-y)      ASSUME_YES=1 ;;
    *) echo "unknown option: $a"; exit 2 ;;
  esac
done

# Build the list of targets that actually exist.
TARGETS=()
add() { [ -e "$1" ] && TARGETS+=("$1"); }

add "$PROJECT/.venv"
add "$PROJECT/app.log"
add "$PROJECT/__pycache__"
add "$PROJECT/engines/__pycache__"
if [ "$KEEP_MODELS" -eq 0 ]; then
  add "$HOME/.local/share/argos-translate"
  add "$HOME/.local/cache/argos-translate"
  add "$HOME/.config/argos-translate"
fi

# Optional: LLM weights this app may have downloaded into the *shared* HF cache.
# IMPORTANT: only the exact model repos referenced by this app are removed —
# NOT every gemma-4 in the cache (you may have many unrelated ones).
APP_HF_MODELS=(
  "models--Rapid42--gemma-4-E2B-it-MLX"            # MLX engine default
  "models--Rapid42--gemma-4-E4B-it-MLX"            # documented "better quality" alt
  "models--unsloth--gemma-4-E2B-it-UD-MLX-4bit"    # documented "smaller" alt
)
LLM_TARGETS=()
if [ "$REMOVE_LLM" -eq 1 ]; then
  HUB="$HOME/.cache/huggingface/hub"
  for name in "${APP_HF_MODELS[@]}"; do
    [ -d "$HUB/$name" ] && LLM_TARGETS+=("$HUB/$name")
  done
fi

if [ "${#TARGETS[@]}" -eq 0 ] && [ "${#LLM_TARGETS[@]}" -eq 0 ]; then
  echo "Nothing to remove — already clean."
  exit 0
fi

echo "The following will be removed:"
for t in "${TARGETS[@]}" "${LLM_TARGETS[@]}"; do
  printf "  %-6s  %s\n" "$(du -sh "$t" 2>/dev/null | cut -f1)" "$t"
done
echo

if [ "$ASSUME_YES" -eq 0 ]; then
  read -r -p "Proceed? [y/N] " ans
  case "$ans" in y|Y|yes|YES) ;; *) echo "Aborted."; exit 1 ;; esac
fi

# Stop a running instance (whatever is bound to the app's port).
PIDS="$(lsof -ti tcp:8765 2>/dev/null || true)"
[ -n "$PIDS" ] && { echo "Stopping running app…"; kill $PIDS 2>/dev/null || true; }

for t in "${TARGETS[@]}" "${LLM_TARGETS[@]}"; do
  rm -rf "$t" && echo "removed: $t"
done

# Drop the app's Launch Services registration (ignore errors).
LSREG="/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister"
[ -x "$LSREG" ] && "$LSREG" -u "$PROJECT/auto-translator.app" 2>/dev/null || true

echo
echo "Done. To finish removing the app entirely:"
echo "  • Drag auto-translator.app out of the Dock if you added it."
echo "  • Delete this folder:  rm -rf \"$PROJECT\""
