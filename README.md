# Travel Agent

Standalone CLI that scrapes Polish travel portals, extracts concrete offers with an LLM, deduplicates across sites, and prints the cheapest deals per destination ordered by departure date.

This is a **separate project** from [gmail-agent](https://github.com/krzysztofras666/gmail-agent).
Repo: **https://github.com/krzysztofras666/travel-agent**

See also **[wizzair/](wizzair/)** — a sibling CLI for searching Wizz Air flights.

It lives in a sibling `../gmail-agent/` folder locally and can share the same
`OPENAI_API_KEY` and Gmail OAuth tokens for the daily email digest.

## Quick start (macOS)

```bash
cd ~/travel-agent
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
cp .env.example .env          # add OPENAI_API_KEY
.venv/bin/python -m travel_agent list-sites
.venv/bin/python -m travel_agent run --max-per-destination 1
```

If `python -m travel_agent` fails with `No module named 'google.auth'`, you are
using system Python instead of the venv. Always run `.venv/bin/python -m travel_agent …`
or `source .venv/bin/activate` first.

## Commands

```bash
python -m travel_agent list-sites
python -m travel_agent run
python -m travel_agent run --site itaka --site rpl
python -m travel_agent run --json > deals.json
python -m travel_agent run --max-per-destination 1
python -m travel_agent run --no-diagnostics
python -m travel_agent run --no-browser
python -m travel_agent run --browser-all
python -m travel_agent send --dry-run
python -m travel_agent preview-email --out /tmp/preview.html
```

## Daily email digest (08:00)

The digest is a styled HTML email with a clickable link for **every offer**
(destination title + “Zobacz ofertę” button). Default recipients:

- `andalath@gmail.com`
- `katarzyna.dyngosz@gmail.com`
- `goniaras@gmail.com`

### One-time Gmail setup

```bash
cd ~/gmail-agent
source .venv/bin/activate
python -m gmail_agent auth --account andalath@gmail.com
```

### Send once manually

```bash
cd ~/travel-agent
source .venv/bin/activate
python -m travel_agent send
python -m travel_agent preview-email --out logs/last_email.html
```

### Schedule every day at 08:00 (macOS launchd)

```bash
cd ~/travel-agent
./scripts/install_travel_schedule.sh
./scripts/run_travel_daily.sh --dry-run
launchctl kickstart gui/$(id -u)/com.travel-agent.daily
```

Logs: `logs/travel_run.log`, `logs/last_email.html`

### Stop scheduled emails (disable agent)

On your Mac, from the travel-agent repo root:

```bash
./scripts/disable_agent.sh
```

This removes launchd jobs for travel (08:00) and wizzair (08:00 / 13:00), and sets
`TRAVEL_AGENT_ENABLED=0`, `TRAVEL_EMAIL_ENABLED=0`, `WIZZAIR_AGENT_ENABLED=0`, and
`WIZZAIR_EMAIL_ENABLED=0` in `.env` and `wizzair/.env`. Manual `send` commands refuse
to email until you run `./scripts/enable_agent.sh` and reinstall schedules.

## Configuration

Environment variables (`.env` supported):

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | Required |
| `TRAVEL_OPENAI_MODEL` | `OPENAI_MODEL` or `gpt-4o-mini` | Extraction model |
| `TRAVEL_HTTP_TIMEOUT` | `20` | HTTP timeout (seconds) |
| `TRAVEL_FETCH_CONCURRENCY` | `6` | Max parallel HTTP requests |
| `TRAVEL_MAX_TEXT_CHARS` | `18000` | Per-site LLM input cap |
| `TRAVEL_MAX_OFFERS_PER_DEST` | `3` | Cheapest N per destination |
| `TRAVEL_BROWSER_RETRY_MIN_CHARS` | `2000` | Trigger browser fallback below this |
| `TRAVEL_EMAIL_FROM` | `andalath@gmail.com` | Digest sender |
| `TRAVEL_EMAIL_TO` | configured list | Comma-separated recipients |
| `GMAIL_TOKEN_DIR` | `~/.config/gmail-agent` | Where gmail-agent stores OAuth tokens |
| `TRAVEL_AGENT_ENABLED` | `1` | `0` skips launchd runs and blocks `send` |
| `TRAVEL_EMAIL_ENABLED` | `1` | `0` blocks Gmail send (dry-run still works) |

## Project layout

```
/travel-agent/
├── travel_agent/       # Python package
│   ├── fetch.py        # httpx + Playwright fallback
│   ├── extract.py      # LLM JSON extraction
│   ├── aggregate.py    # dedupe + cheapest-per-destination
│   └── __main__.py     # CLI entry point
├── scripts/            # macOS launchd helpers
├── logs/               # runtime output (gitignored)
├── requirements.txt
└── .env.example
```

## Scheduled daily run (macOS)

```bash
./scripts/install_travel_schedule.sh
./scripts/run_travel_daily.sh --dry-run
launchctl kickstart gui/$(id -u)/com.travel-agent.daily
```

## Gmail integration

`travel_agent send` uses Gmail OAuth tokens created by gmail-agent:

```bash
# in gmail-agent repo
python -m gmail_agent auth
```

No new Google credentials are needed in this project if tokens already exist under `GMAIL_TOKEN_DIR`.
