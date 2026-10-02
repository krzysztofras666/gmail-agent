#!/usr/bin/env bash
# shellcheck shell=bash
set_env_flag() {
  local file="$1"
  local key="$2"
  local value="$3"
  touch "$file"
  if grep -q "^${key}=" "$file" 2>/dev/null; then
    if [[ "$(uname)" == "Darwin" ]]; then
      sed -i '' "s/^${key}=.*/${key}=${value}/" "$file"
    else
      sed -i "s/^${key}=.*/${key}=${value}/" "$file"
    fi
  else
    echo "${key}=${value}" >>"$file"
  fi
}
