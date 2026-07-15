#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_SRC="$ROOT/scripts/com.travel-agent.daily.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.travel-agent.daily.plist"

mkdir -p "$HOME/Library/LaunchAgents"
sed "s|__PROJECT_ROOT__|$ROOT|g" "$PLIST_SRC" >"$PLIST_DEST"
launchctl bootout "gui/$(id -u)/com.travel-agent.daily" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DEST"
launchctl enable "gui/$(id -u)/com.travel-agent.daily"
echo "Installed $PLIST_DEST"
