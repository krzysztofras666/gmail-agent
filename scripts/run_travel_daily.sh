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

case "${TRAVEL_AGENT_ENABLED:-1}" in
  0|false|FALSE|no|NO|off|OFF)
    echo "travel_agent disabled (TRAVEL_AGENT_ENABLED). Skipping scheduled run."
    exit 0
    ;;
esac

PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3 || command -v python)"
fi

mkdir -p logs
LOG="logs/travel_run.log"

{
  echo "=== $(date -Iseconds) travel_agent daily run ==="
  "$PYTHON" -m travel_agent send "$@"
} >>"$LOG" 2>&1

echo "Run complete. See $LOG"
