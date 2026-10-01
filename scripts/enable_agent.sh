#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/_env_flag.sh"

set_env_flag "$ROOT/.env" TRAVEL_AGENT_ENABLED 1
set_env_flag "$ROOT/.env" TRAVEL_EMAIL_ENABLED 1
if [[ -d "$ROOT/wizzair" ]]; then
  set_env_flag "$ROOT/wizzair/.env" WIZZAIR_AGENT_ENABLED 1
  set_env_flag "$ROOT/wizzair/.env" WIZZAIR_EMAIL_ENABLED 1
fi

echo "Re-enabled travel_agent in .env (and wizzair when wizzair/ exists)."
echo "To resume automatic emails, reinstall schedules:"
echo "  ./scripts/install_travel_schedule.sh"
if [[ -d "$ROOT/wizzair/scripts" ]]; then
  echo "  ./wizzair/scripts/install_wizzair_schedule.sh"
fi
