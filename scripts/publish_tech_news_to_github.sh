#!/usr/bin/env bash
set -euo pipefail

# Clone the standalone project branch from gmail-agent and publish it to
# https://github.com/krzysztofras666/tech-news-agent
#
# Requires: gh auth login (as krzysztofras666) or GH_PAT with repo scope.

REPO="krzysztofras666/tech-news-agent"
REPO_URL="https://github.com/${REPO}.git"
SOURCE_BRANCH="tech-news-agent-main"
WORKDIR="${1:-/tmp/tech-news-agent-publish}"

repo_exists() {
  curl -fsS "https://api.github.com/repos/${REPO}" >/dev/null 2>&1
}

create_repo() {
  if ! command -v gh >/dev/null 2>&1; then
    echo "GitHub CLI (gh) is required. Install: https://cli.github.com/"
    return 1
  fi
  gh repo create "$REPO" \
    --public \
    --description "Fetch tech headlines from RSS/API sources and email a daily digest"
}

clone_source() {
  rm -rf "$WORKDIR"
  git clone --branch "$SOURCE_BRANCH" --single-branch \
    "https://github.com/krzysztofras666/gmail-agent.git" "$WORKDIR"
  cd "$WORKDIR"
}

publish() {
  clone_source
  if repo_exists; then
    echo "Repository exists: https://github.com/${REPO}"
    git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
    git push -u origin HEAD:main --force
  else
    echo "Repository does not exist yet; creating ${REPO}..."
    create_repo
    git remote add origin "$REPO_URL"
    git push -u origin HEAD:main
  fi
  echo "Published to https://github.com/${REPO}"
}

publish
