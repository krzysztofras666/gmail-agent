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
    max_offers_per_dest: int
    user_agent: str
    browser_retry_min_chars: int
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
        openai_model=os.getenv("TRAVEL_OPENAI_MODEL", base_model),
        http_timeout=float(os.getenv("TRAVEL_HTTP_TIMEOUT", "20")),
        fetch_concurrency=int(os.getenv("TRAVEL_FETCH_CONCURRENCY", "6")),
        max_text_chars=int(os.getenv("TRAVEL_MAX_TEXT_CHARS", "18000")),
        max_offers_per_dest=int(os.getenv("TRAVEL_MAX_OFFERS_PER_DEST", "3")),
        user_agent=os.getenv("TRAVEL_USER_AGENT", DEFAULT_USER_AGENT),
        browser_retry_min_chars=int(os.getenv("TRAVEL_BROWSER_RETRY_MIN_CHARS", "2000")),
        email_from=os.getenv("TRAVEL_EMAIL_FROM", "andalath@gmail.com"),
        email_to=_split_emails(os.getenv("TRAVEL_EMAIL_TO", default_to)),
        gmail_token_dir=os.path.expanduser(
            os.getenv("GMAIL_TOKEN_DIR", "~/.config/gmail-agent")
        ),
    )
