#!/usr/bin/env bash
# Uninstall auto-translator's local data. Safe by default: only removes things
# this app created. The project folder itself is left in place (delete it
# yourself afterwards if you want).
#
# Usage:
#   ./uninstall.sh                 # venv, logs, caches, Argos language models
#   ./uninstall.sh --keep-models   # keep downloaded Argos language models
#   ./uninstall.sh --yes           # don't ask for confirmation
set -e
cd "$(dirname "$0")"
PROJECT="$(pwd)"

KEEP_MODELS=0; ASSUME_YES=0
for a in "$@"; do
  case "$a" in
    --keep-models) KEEP_MODELS=1 ;;
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
  add "$HOME/.cache/auto-translator"        # locally-built MLX model(s)
fi

if [ "${#TARGETS[@]}" -eq 0 ]; then
  echo "Nothing to remove — already clean."
  exit 0
fi

echo "The following will be removed:"
for t in "${TARGETS[@]}"; do
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

for t in "${TARGETS[@]}"; do
  rm -rf "$t" && echo "removed: $t"
done

# Drop the app's Launch Services registration (ignore errors).
LSREG="/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister"
[ -x "$LSREG" ] && "$LSREG" -u "$PROJECT/auto-translator.app" 2>/dev/null || true

echo
echo "Done. To finish removing the app entirely:"
echo "  • Drag auto-translator.app out of the Dock if you added it."
echo "  • Delete this folder:  rm -rf \"$PROJECT\""
