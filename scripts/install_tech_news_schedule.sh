#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_SRC="$ROOT/scripts/com.tech-news-agent.daily.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.tech-news-agent.daily.plist"

sed "s|__PROJECT_ROOT__|$ROOT|g" "$PLIST_SRC" >"$PLIST_DST"
launchctl bootout "gui/$(id -u)/com.tech-news-agent.daily" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
echo "Installed $PLIST_DST (daily at 09:00)"
