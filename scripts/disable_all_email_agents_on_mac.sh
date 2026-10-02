#!/usr/bin/env bash
# Stop scheduled runs and outbound email for travel-agent, wizzair, and tech-news-agent.
# Safe to run before or after pulling the latest disable_agent.sh changes.
set -euo pipefail

set_env_flag() {
  local file="$1"
  local key="$2"
  local value="$3"
  [[ -f "$file" ]] || touch "$file"
  if grep -q "^${key}=" "$file" 2>/dev/null; then
    sed -i '' "s/^${key}=.*/${key}=${value}/" "$file"
  else
    echo "${key}=${value}" >>"$file"
  fi
}

disable_launchd() {
  local label="$1"
  launchctl bootout "gui/$(id -u)/${label}" 2>/dev/null || true
}

remove_plist() {
  local name="$1"
  rm -f "$HOME/Library/LaunchAgents/${name}"
}

TRAVEL_DIR="${TRAVEL_AGENT_DIR:-$HOME/travel-agent}"
TECH_DIR="${TECH_NEWS_AGENT_DIR:-$HOME/tech-news-agent}"

echo "Removing macOS launchd jobs (if installed)..."
for label in \
  com.travel-agent.daily \
  com.wizzair.daily \
  com.wizzair.afternoon \
  com.tech-news-agent.daily \
  com.gmail-agent.daily; do
  disable_launchd "$label"
done
remove_plist com.travel-agent.daily.plist
remove_plist com.wizzair.daily.plist
remove_plist com.wizzair.afternoon.plist
remove_plist com.tech-news-agent.daily.plist
remove_plist com.gmail-agent.daily.plist

if [[ -x "$TRAVEL_DIR/scripts/disable_agent.sh" ]]; then
  echo "Running $TRAVEL_DIR/scripts/disable_agent.sh ..."
  (cd "$TRAVEL_DIR" && ./scripts/disable_agent.sh)
elif [[ -d "$TRAVEL_DIR" ]]; then
  echo "Travel-agent repo at $TRAVEL_DIR (no disable_agent.sh yet) — setting .env flags only."
  set_env_flag "$TRAVEL_DIR/.env" TRAVEL_AGENT_ENABLED 0
  set_env_flag "$TRAVEL_DIR/.env" TRAVEL_EMAIL_ENABLED 0
  if [[ -d "$TRAVEL_DIR/wizzair" ]]; then
    set_env_flag "$TRAVEL_DIR/wizzair/.env" WIZZAIR_AGENT_ENABLED 0
    set_env_flag "$TRAVEL_DIR/wizzair/.env" WIZZAIR_EMAIL_ENABLED 0
  fi
  [[ -x "$TRAVEL_DIR/scripts/uninstall_travel_schedule.sh" ]] && \
    (cd "$TRAVEL_DIR" && ./scripts/uninstall_travel_schedule.sh) || true
  [[ -x "$TRAVEL_DIR/wizzair/scripts/uninstall_wizzair_schedule.sh" ]] && \
    (cd "$TRAVEL_DIR/wizzair" && ./scripts/uninstall_wizzair_schedule.sh) || true
else
  echo "No travel-agent directory at $TRAVEL_DIR (set TRAVEL_AGENT_DIR to override)."
fi

if [[ -x "$TECH_DIR/scripts/disable_agent.sh" ]]; then
  echo "Running $TECH_DIR/scripts/disable_agent.sh ..."
  (cd "$TECH_DIR" && ./scripts/disable_agent.sh)
elif [[ -d "$TECH_DIR" ]]; then
  echo "Tech-news repo at $TECH_DIR (no disable_agent.sh yet) — setting .env flags only."
  set_env_flag "$TECH_DIR/.env" TECH_NEWS_AGENT_ENABLED 0
  set_env_flag "$TECH_DIR/.env" TECH_NEWS_EMAIL_ENABLED 0
  [[ -x "$TECH_DIR/scripts/uninstall_tech_news_schedule.sh" ]] && \
    (cd "$TECH_DIR" && ./scripts/uninstall_tech_news_schedule.sh) || true
else
  echo "No tech-news-agent directory at $TECH_DIR (set TECH_NEWS_AGENT_DIR to override)."
fi

echo ""
echo "Done. Scheduled agent emails should be stopped."
echo "Gmail Agent only creates drafts and does not send mail; its launchd job was removed if present."
