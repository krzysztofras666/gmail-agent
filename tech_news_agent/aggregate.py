from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from tech_news_agent.models import TechArticle


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in {"ref", "source"}
    ]
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme, parsed.netloc.lower(), path, "", urlencode(query), ""))


def _article_key(article: TechArticle) -> str:
    normalized = _normalize_url(article.url)
    if normalized:
        return normalized
    return re.sub(r"\s+", " ", article.title.casefold()).strip()


def _parse_published_at(value: str) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
    ):
        try:
            parsed = datetime.strptime(value, fmt)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _within_lookback(article: TechArticle, *, hours_lookback: int) -> bool:
    published = _parse_published_at(article.published_at)
    if published is None:
        return True
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_lookback)
    return published >= cutoff


def aggregate_articles(
    articles: list[TechArticle],
    *,
    max_articles: int,
    max_per_topic: int,
    hours_lookback: int,
) -> list[TechArticle]:
    deduped: dict[str, TechArticle] = {}
    for article in articles:
        if not _within_lookback(article, hours_lookback=hours_lookback):
            continue
        key = _article_key(article)
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = article
            continue
        existing_score = existing.score or 0
        new_score = article.score or 0
        if new_score > existing_score:
            deduped[key] = article

    by_topic: dict[str, list[TechArticle]] = {}
    for article in deduped.values():
        primary_topic = article.topics[0] if article.topics else "general"
        by_topic.setdefault(primary_topic.casefold(), []).append(article)

    selected: list[TechArticle] = []
    for topic_articles in by_topic.values():
        topic_articles.sort(key=_sort_key, reverse=True)
        selected.extend(topic_articles[:max_per_topic])

    selected.sort(key=_sort_key, reverse=True)
    return selected[:max_articles]


def _sort_key(article: TechArticle) -> tuple:
    published = _parse_published_at(article.published_at)
    published_ts = published.timestamp() if published else 0.0
    return (published_ts, article.score or 0)
