#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

REPO="krzysztofras666/travel-agent"
REPO_URL="https://github.com/${REPO}.git"

repo_exists() {
  curl -fsS "https://api.github.com/repos/${REPO}" >/dev/null 2>&1
}

ensure_remote() {
  if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$REPO_URL"
  else
    git remote add origin "$REPO_URL"
  fi
}

create_repo() {
  if ! command -v gh >/dev/null 2>&1; then
    echo "GitHub CLI (gh) is required to create the repository."
    echo "Install: https://cli.github.com/"
    return 1
  fi
  gh repo create "$REPO" \
    --public \
    --source=. \
    --remote=origin \
    --description "Scrape Polish travel portals and surface the cheapest last-minute deals"
}

if repo_exists; then
  echo "Repository exists: https://github.com/${REPO}"
  ensure_remote
  git push -u origin main
  echo "Published to https://github.com/${REPO}"
  exit 0
fi

echo "Repository does not exist yet; creating ${REPO}..."
if create_repo; then
  git push -u origin main
  echo "Published to https://github.com/${REPO}"
  exit 0
fi

echo ""
echo "Could not create the repository from this environment."
echo "Create it manually, then re-run this script:"
echo ""
echo "  https://github.com/new?name=travel-agent&description=Scrape+Polish+travel+portals"
echo ""
echo "Leave README / .gitignore unchecked, then:"
echo "  ./scripts/publish_to_github.sh"
exit 1
