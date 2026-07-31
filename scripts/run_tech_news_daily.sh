#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

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
