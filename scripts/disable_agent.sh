#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/_env_flag.sh"

"$ROOT/scripts/uninstall_travel_schedule.sh"
if [[ -d "$ROOT/wizzair/scripts" ]]; then
  "$ROOT/wizzair/scripts/uninstall_wizzair_schedule.sh"
fi

set_env_flag "$ROOT/.env" TRAVEL_AGENT_ENABLED 0
set_env_flag "$ROOT/.env" TRAVEL_EMAIL_ENABLED 0
if [[ -d "$ROOT/wizzair" ]]; then
  set_env_flag "$ROOT/wizzair/.env" WIZZAIR_AGENT_ENABLED 0
  set_env_flag "$ROOT/wizzair/.env" WIZZAIR_EMAIL_ENABLED 0
fi

echo "Disabled travel_agent (and wizzair when present):"
echo "  - Removed macOS launchd jobs (travel 08:00; wizzair 08:00/13:00 if installed)"
echo "  - Set TRAVEL_AGENT_ENABLED=0 and TRAVEL_EMAIL_ENABLED=0 in .env"
if [[ -d "$ROOT/wizzair" ]]; then
  echo "  - Set WIZZAIR_AGENT_ENABLED=0 and WIZZAIR_EMAIL_ENABLED=0 in wizzair/.env"
fi
echo ""
echo "Manual 'send' commands will refuse to email until you run scripts/enable_agent.sh"
