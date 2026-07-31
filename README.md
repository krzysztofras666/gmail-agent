# Agents

This repo hosts CLI agents that share a single `.venv`, `OPENAI_API_KEY`, and
Gmail OAuth tokens (from [gmail-agent](https://github.com/krzysztofras666/gmail-agent)):

- **`travel_agent`** — scrapes Polish travel portals and emails the cheapest deals.
- **`tech_news_agent`** — fetches tech headlines from RSS/API sources and emails a daily digest.

---

# Travel Agent

Standalone CLI that scrapes Polish travel portals, extracts concrete offers with an LLM, deduplicates across sites, and prints the cheapest deals per destination ordered by departure date.

This is a **separate project** from [gmail-agent](https://github.com/krzysztofras666/gmail-agent).
Repo: **https://github.com/krzysztofras666/travel-agent**

It lives in a sibling `../gmail-agent/` folder locally and can share the same
`OPENAI_API_KEY` and Gmail OAuth tokens for the daily email digest.

## Quick start

```bash
cd /path/to/travel-agent   # sibling of gmail-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # optional but recommended
cp .env.example .env          # add OPENAI_API_KEY
python -m travel_agent list-sites
python -m travel_agent run --site itaka --max-per-destination 1
```

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

---

# Tech News Agent

`tech_news_agent` fetches headlines from Hacker News (API), TechCrunch, Ars Technica,
The Verge, Lobsters, GitHub Blog, and an HN Algolia AI/ML feed. RSS sources are
parsed with an LLM; API sources are structured directly (no LLM cost for HN).

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add OPENAI_API_KEY
python -m tech_news_agent list-sources
python -m tech_news_agent run --source hn --source techcrunch
```

## Commands

```bash
python -m tech_news_agent list-sources
python -m tech_news_agent run
python -m tech_news_agent run --source hn --source arstechnica
python -m tech_news_agent run --json > news.json
python -m tech_news_agent run --max-articles 15
python -m tech_news_agent run --no-diagnostics
python -m tech_news_agent send --dry-run
python -m tech_news_agent preview-email --out /tmp/preview.html
```

## Configured sources

| ID | Source | Kind |
| --- | --- | --- |
| `hn` | Hacker News top stories | API |
| `techcrunch` | TechCrunch | RSS |
| `arstechnica` | Ars Technica | RSS |
| `theverge` | The Verge | RSS |
| `lobsters` | Lobsters | RSS |
| `github_blog` | GitHub Blog | RSS |
| `hn_algolia` | HN — AI/ML (Algolia) | API |

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | Required for RSS extraction |
| `TECH_NEWS_OPENAI_MODEL` | `OPENAI_MODEL` or `gpt-4o-mini` | Extraction model |
| `TECH_NEWS_HTTP_TIMEOUT` | `20` | HTTP timeout (seconds) |
| `TECH_NEWS_FETCH_CONCURRENCY` | `6` | Max parallel requests |
| `TECH_NEWS_MAX_TEXT_CHARS` | `18000` | Per-source LLM input cap |
| `TECH_NEWS_MAX_ARTICLES` | `30` | Max articles in final digest |
| `TECH_NEWS_MAX_PER_TOPIC` | `5` | Max articles per primary topic |
| `TECH_NEWS_HOURS_LOOKBACK` | `48` | Drop articles older than this |
| `TECH_NEWS_HN_TOP_STORIES` | `25` | How many HN top stories to fetch |
| `TECH_NEWS_EMAIL_FROM` | `andalath@gmail.com` | Digest sender |
| `TECH_NEWS_EMAIL_TO` | configured list | Comma-separated recipients |
| `GMAIL_TOKEN_DIR` | `~/.config/gmail-agent` | OAuth token directory |

## Scheduled daily run (macOS)

Runs at **09:00 local time** (15 minutes after the travel agent):

```bash
./scripts/install_tech_news_schedule.sh
./scripts/run_tech_news_daily.sh --dry-run
launchctl kickstart gui/$(id -u)/com.tech-news-agent.daily
```

Logs: `logs/tech_news_run.log`, `logs/last_tech_news_email.html`.
