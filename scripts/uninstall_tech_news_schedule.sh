#!/usr/bin/env bash
set -euo pipefail

PLIST_DST="$HOME/Library/LaunchAgents/com.tech-news-agent.daily.plist"
launchctl bootout "gui/$(id -u)/com.tech-news-agent.daily" 2>/dev/null || true
rm -f "$PLIST_DST"
echo "Removed $PLIST_DST"
