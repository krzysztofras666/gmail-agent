#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/_env_flag.sh"

set_env_flag "$ROOT/.env" TECH_NEWS_AGENT_ENABLED 1
set_env_flag "$ROOT/.env" TECH_NEWS_EMAIL_ENABLED 1

echo "Re-enabled tech_news_agent in .env."
echo "To resume automatic emails, reinstall the schedule:"
echo "  ./scripts/install_tech_news_schedule.sh"
