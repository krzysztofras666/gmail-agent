#!/usr/bin/env bash
set -euo pipefail

# Clone the travel-agent export branch from gmail-agent and push it to
# https://github.com/krzysztofras666/travel-agent
#
# Requires: gh auth login (as krzysztofras666) or GH_PAT with repo scope.
#
# Note: the travel-agent repo may contain additional projects (e.g. wizzair).
# This script force-pushes the travel_agent-only export branch. Only run it if
# you intend to replace main with that snapshot.

REPO="krzysztofras666/travel-agent"
REPO_URL="https://github.com/${REPO}.git"
SOURCE_BRANCH="travel-agent-main"
WORKDIR="${1:-/tmp/travel-agent-publish}"

repo_exists() {
  curl -fsS "https://api.github.com/repos/${REPO}" >/dev/null 2>&1
}

clone_source() {
  rm -rf "$WORKDIR"
  git clone --branch "$SOURCE_BRANCH" --single-branch \
    "https://github.com/krzysztofras666/gmail-agent.git" "$WORKDIR"
  cd "$WORKDIR"
}

publish() {
  clone_source
  if ! repo_exists; then
    echo "Repository not found: https://github.com/${REPO}"
    echo "Create it first, then re-run this script."
    exit 1
  fi
  echo "Publishing to https://github.com/${REPO}"
  git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
  git push -u origin HEAD:main --force
  echo "Published to https://github.com/${REPO}"
}

publish
