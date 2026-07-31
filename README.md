# Tech News Agent

Standalone CLI that fetches tech headlines from RSS/API sources, extracts structured
articles with an LLM where needed, deduplicates across sources, and emails a daily digest.

This is a **separate project** from [gmail-agent](https://github.com/krzysztofras666/gmail-agent).
Repo: **https://github.com/krzysztofras666/tech-news-agent**

It lives in a sibling `../gmail-agent/` folder locally and can share the same
`OPENAI_API_KEY` and Gmail OAuth tokens for the daily email digest.

## Quick start

```bash
cd /path/to/tech-news-agent   # sibling of gmail-agent
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

HN and Algolia sources are parsed directly (no LLM cost). RSS feeds use structured
OpenAI extraction.

## Configuration

Environment variables (`.env` supported):

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

## Project layout

```
/tech-news-agent/
├── tech_news_agent/    # Python package
│   ├── fetch.py        # httpx + HN/Algolia APIs
│   ├── extract.py      # LLM JSON extraction (RSS)
│   ├── aggregate.py    # dedupe + topic caps
│   └── __main__.py     # CLI entry point
├── scripts/            # macOS launchd helpers
├── logs/               # runtime output (gitignored)
├── requirements.txt
└── .env.example
```

## Scheduled daily run (macOS)

Runs at **09:00 local time**:

```bash
./scripts/install_tech_news_schedule.sh
./scripts/run_tech_news_daily.sh --dry-run
launchctl kickstart gui/$(id -u)/com.tech-news-agent.daily
```

Logs: `logs/tech_news_run.log`, `logs/last_tech_news_email.html`.

## Gmail integration

`tech_news_agent send` uses Gmail OAuth tokens created by gmail-agent:

```bash
# in gmail-agent repo
python -m gmail_agent auth
```

No new Google credentials are needed in this project if tokens already exist under `GMAIL_TOKEN_DIR`.
