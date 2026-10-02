#!/usr/bin/env bash
set -euo pipefail

launchctl bootout "gui/$(id -u)/com.wizzair.daily" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/com.wizzair.afternoon" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/com.wizzair.daily.plist"
rm -f "$HOME/Library/LaunchAgents/com.wizzair.afternoon.plist"
echo "Removed com.wizzair.daily and com.wizzair.afternoon schedules"
