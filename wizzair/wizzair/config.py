from __future__ import annotations

import os
from dataclasses import dataclass

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

WALLETS_URL = "https://multipass.wizzair.com/pl/w6/subscriptions/spa/private-page/wallets"


def default_session_path() -> Path:
    return Path.home() / ".config" / "wizzair" / "storage_state.json"


@dataclass(frozen=True)
class Settings:
    email: str
    password: str
    pass_id: str | None
    origins: tuple[str, ...]
    days_ahead: int
    destination_filter: tuple[str, ...]
    http_timeout: float
    search_concurrency: int
    locale: str
    user_agent: str
    headless: bool
    use_chrome: bool
    fast_scan: bool
    storage_state_path: Path
    email_from: str
    email_to: list[str]
    gmail_token_dir: str
    agent_enabled: bool
    email_enabled: bool


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip().upper() for part in value.split(",") if part.strip())


def _split_emails(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _env_bool(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def get_settings() -> Settings:
    email = os.getenv("WIZZAIR_EMAIL", "")
    password = os.getenv("WIZZAIR_PASSWORD", "")
    if not email or not password:
        raise RuntimeError(
            "WIZZAIR_EMAIL and WIZZAIR_PASSWORD are required. Set them in wizzair/.env"
        )

    default_to = "katarzyna.dyngosz@gmail.com,andalath@gmail.com"
    return Settings(
        email=email,
        password=password,
        pass_id=os.getenv("WIZZAIR_PASS_ID") or None,
        origins=_split_csv(os.getenv("WIZZAIR_ORIGINS", "KRK,KTW")),
        days_ahead=int(os.getenv("WIZZAIR_DAYS", "4")),
        destination_filter=_split_csv(os.getenv("WIZZAIR_DESTINATIONS", "")),
        http_timeout=float(os.getenv("WIZZAIR_HTTP_TIMEOUT", "60")),
        search_concurrency=int(os.getenv("WIZZAIR_SEARCH_CONCURRENCY", "4")),
        locale=os.getenv("WIZZAIR_LOCALE", "pl"),
        user_agent=os.getenv("WIZZAIR_USER_AGENT", DEFAULT_USER_AGENT),
        headless=os.getenv("WIZZAIR_HEADLESS", "true").lower() in {"1", "true", "yes"},
        use_chrome=os.getenv("WIZZAIR_USE_CHROME", "true").lower() in {"1", "true", "yes"},
        fast_scan=os.getenv("WIZZAIR_FAST_SCAN", "false").lower() in {"1", "true", "yes"},
        storage_state_path=Path(
            os.path.expanduser(os.getenv("WIZZAIR_STORAGE_STATE", str(default_session_path())))
        ),
        email_from=os.getenv("WIZZAIR_EMAIL_FROM", "andalath@gmail.com"),
        email_to=_split_emails(os.getenv("WIZZAIR_EMAIL_TO", default_to)),
        gmail_token_dir=os.path.expanduser(
            os.getenv("GMAIL_TOKEN_DIR", "~/.config/gmail-agent")
        ),
        agent_enabled=_env_bool("WIZZAIR_AGENT_ENABLED", True),
        email_enabled=_env_bool("WIZZAIR_EMAIL_ENABLED", True),
    )
