#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required. Install: https://cli.github.com/"
  exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "Remote origin already set:"
  git remote -v
else
  gh repo create krzysztofras666/travel-agent \
    --public \
    --source=. \
    --remote=origin \
    --description "Scrape Polish travel portals and surface the cheapest last-minute deals"
fi

git push -u origin main
echo "Published to https://github.com/krzysztofras666/travel-agent"
