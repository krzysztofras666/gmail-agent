#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

case "${TECH_NEWS_AGENT_ENABLED:-1}" in
  0|false|FALSE|no|NO|off|OFF)
    echo "tech_news_agent disabled (TECH_NEWS_AGENT_ENABLED). Skipping scheduled run."
    exit 0
    ;;
esac

if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

mkdir -p logs
LOG="logs/tech_news_run.log"

{
  echo "=== $(date -Iseconds) tech_news_agent daily run ==="
  python -m tech_news_agent send "$@"
} >>"$LOG" 2>&1

echo "Run complete. See $LOG"
