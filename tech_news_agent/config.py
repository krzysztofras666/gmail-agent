from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    http_timeout: float
    fetch_concurrency: int
    max_text_chars: int
    max_articles: int
    max_per_topic: int
    hours_lookback: int
    hn_top_stories: int
    user_agent: str
    email_from: str
    email_to: list[str]
    gmail_token_dir: str


def _split_emails(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def get_settings() -> Settings:
    base_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    default_to = "andalath@gmail.com, goniaras@gmail.com, katarzyna.dyngosz@gmail.com"
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required. Set it in .env or the environment.")

    return Settings(
        openai_api_key=api_key,
        openai_model=os.getenv("TECH_NEWS_OPENAI_MODEL", base_model),
        http_timeout=float(os.getenv("TECH_NEWS_HTTP_TIMEOUT", "20")),
        fetch_concurrency=int(os.getenv("TECH_NEWS_FETCH_CONCURRENCY", "6")),
        max_text_chars=int(os.getenv("TECH_NEWS_MAX_TEXT_CHARS", "18000")),
        max_articles=int(os.getenv("TECH_NEWS_MAX_ARTICLES", "30")),
        max_per_topic=int(os.getenv("TECH_NEWS_MAX_PER_TOPIC", "5")),
        hours_lookback=int(os.getenv("TECH_NEWS_HOURS_LOOKBACK", "48")),
        hn_top_stories=int(os.getenv("TECH_NEWS_HN_TOP_STORIES", "25")),
        user_agent=os.getenv("TECH_NEWS_USER_AGENT", DEFAULT_USER_AGENT),
        email_from=os.getenv("TECH_NEWS_EMAIL_FROM", "andalath@gmail.com"),
        email_to=_split_emails(os.getenv("TECH_NEWS_EMAIL_TO", default_to)),
        gmail_token_dir=os.path.expanduser(
            os.getenv("GMAIL_TOKEN_DIR", "~/.config/gmail-agent")
        ),
    )
