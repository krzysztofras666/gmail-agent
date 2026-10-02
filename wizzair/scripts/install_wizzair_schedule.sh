#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MORNING_SRC="$ROOT/scripts/com.wizzair.daily.plist"
AFTERNOON_SRC="$ROOT/scripts/com.wizzair.afternoon.plist"
MORNING_DEST="$HOME/Library/LaunchAgents/com.wizzair.daily.plist"
AFTERNOON_DEST="$HOME/Library/LaunchAgents/com.wizzair.afternoon.plist"

mkdir -p "$HOME/Library/LaunchAgents" "$ROOT/logs"
sed "s|__PROJECT_ROOT__|$ROOT|g" "$MORNING_SRC" >"$MORNING_DEST"
sed "s|__PROJECT_ROOT__|$ROOT|g" "$AFTERNOON_SRC" >"$AFTERNOON_DEST"

launchctl bootout "gui/$(id -u)/com.wizzair.daily" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/com.wizzair.afternoon" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$MORNING_DEST"
launchctl bootstrap "gui/$(id -u)" "$AFTERNOON_DEST"
launchctl enable "gui/$(id -u)/com.wizzair.daily"
launchctl enable "gui/$(id -u)/com.wizzair.afternoon"

if ! launchctl print "gui/$(id -u)/com.wizzair.daily" >/dev/null 2>&1; then
  echo "ERROR: com.wizzair.daily failed to load. Check paths in $MORNING_DEST" >&2
  exit 1
fi
if ! launchctl print "gui/$(id -u)/com.wizzair.afternoon" >/dev/null 2>&1; then
  echo "ERROR: com.wizzair.afternoon failed to load. Check paths in $AFTERNOON_DEST" >&2
  exit 1
fi

echo "Installed:"
echo "  $MORNING_DEST   (08:00 — pełny digest)"
echo "  $AFTERNOON_DEST (13:00 — tylko zmiany)"
echo ""
echo "Verify:"
echo "  launchctl print gui/\$(id -u)/com.wizzair.daily"
echo "  launchctl print gui/\$(id -u)/com.wizzair.afternoon"
echo ""
echo "Test run (bez wysyłki maila):"
echo "  $ROOT/scripts/run_wizzair_morning.sh --dry-run"
echo ""
echo "Full setup check:"
echo "  cd $ROOT && source .venv/bin/activate && python -m wizzair doctor"
