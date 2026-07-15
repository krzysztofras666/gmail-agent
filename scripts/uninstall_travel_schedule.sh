#!/usr/bin/env bash
set -euo pipefail

launchctl bootout "gui/$(id -u)/com.travel-agent.daily" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/com.travel-agent.daily.plist"
echo "Uninstalled com.travel-agent.daily"
