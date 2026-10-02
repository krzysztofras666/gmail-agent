#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/_env_flag.sh"

"$ROOT/scripts/uninstall_tech_news_schedule.sh"

set_env_flag "$ROOT/.env" TECH_NEWS_AGENT_ENABLED 0
set_env_flag "$ROOT/.env" TECH_NEWS_EMAIL_ENABLED 0

echo "Disabled tech_news_agent:"
echo "  - Removed macOS launchd job (09:00)"
echo "  - Set TECH_NEWS_AGENT_ENABLED=0 and TECH_NEWS_EMAIL_ENABLED=0 in .env"
echo ""
echo "Manual 'send' commands will refuse to email until you run scripts/enable_agent.sh"
