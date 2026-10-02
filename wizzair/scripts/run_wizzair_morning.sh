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

case "${WIZZAIR_AGENT_ENABLED:-1}" in
  0|false|FALSE|no|NO|off|OFF)
    echo "wizzair disabled (WIZZAIR_AGENT_ENABLED). Skipping morning run."
    exit 0
    ;;
esac

PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3 || command -v python)"
fi

mkdir -p logs
LOG="logs/wizzair_morning.log"

{
  echo "=== $(date '+%Y-%m-%dT%H:%M:%S%z') wizzair morning run ==="
  "$PYTHON" -m wizzair send "$@"
} >>"$LOG" 2>&1

echo "Morning run complete. See $LOG"
