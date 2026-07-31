from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import httpx

from tech_news_agent.config import Settings
from tech_news_agent.models import FetchResult, TechArticle
from tech_news_agent.sources import Source

HN_API = "https://hacker-news.firebaseio.com/v0"


async def fetch_source(settings: Settings, source: Source) -> FetchResult:
    if source.kind == "hn_api":
        return await _fetch_hn_top(settings, source)
    return await _fetch_http(settings, source)


async def fetch_hn_articles(settings: Settings, source: Source) -> list[TechArticle]:
    result = await _fetch_hn_top(settings, source)
    if result.error or not result.text:
        return []
    return _parse_hn_items(result.text, source)


async def fetch_algolia_articles(settings: Settings, source: Source) -> list[TechArticle]:
    result = await _fetch_http(settings, source)
    if result.error or not result.text:
        return []
    return _parse_algolia_json(result.text, source)


async def _fetch_hn_top(settings: Settings, source: Source) -> FetchResult:
    headers = {"User-Agent": settings.user_agent}
    timeout = httpx.Timeout(settings.http_timeout)
    try:
        async with httpx.AsyncClient(headers=headers, timeout=timeout) as client:
            ids_response = await client.get(f"{HN_API}/topstories.json")
            ids_response.raise_for_status()
            story_ids = ids_response.json()[: settings.hn_top_stories]

            sem = asyncio.Semaphore(settings.fetch_concurrency)

            async def fetch_item(story_id: int) -> dict | None:
                async with sem:
                    try:
                        response = await client.get(f"{HN_API}/item/{story_id}.json")
                        response.raise_for_status()
                        return response.json()
                    except Exception:
                        return None

            items = await asyncio.gather(*(fetch_item(story_id) for story_id in story_ids))
            payload = [item for item in items if item and item.get("type") == "story"]
            return FetchResult(source.id, json.dumps(payload), "api", HN_API)
    except Exception as exc:  # noqa: BLE001
        return FetchResult(source.id, "", "api", HN_API, error=str(exc))


async def _fetch_http(settings: Settings, source: Source) -> FetchResult:
    headers = {
        "User-Agent": settings.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }
    timeout = httpx.Timeout(settings.http_timeout)
    last_error = ""
    async with httpx.AsyncClient(
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
        http2=True,
    ) as client:
        for url in source.urls:
            try:
                response = await client.get(url)
                if response.status_code >= 400:
                    last_error = f"HTTP {response.status_code} for {url}"
                    continue
                text = response.text
                if text.strip():
                    return FetchResult(source.id, text, "http", str(response.url))
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
    return FetchResult(source.id, "", "http", source.urls[0] if source.urls else "", error=last_error)


def _parse_hn_items(payload: str, source: Source) -> list[TechArticle]:
    items = json.loads(payload)
    articles: list[TechArticle] = []
    for item in items:
        title = (item.get("title") or "").strip()
        url = (item.get("url") or f"https://news.ycombinator.com/item?id={item.get('id')}").strip()
        if not title:
            continue
        published_at = _unix_to_iso(item.get("time"))
        score = item.get("score")
        author = (item.get("by") or "").strip()
        articles.append(
            TechArticle(
                title=title,
                url=url,
                summary=f"HN score: {score}" if score is not None else "",
                published_at=published_at,
                topics=["hacker-news"],
                source=source.name,
                source_id=source.id,
                author=author,
                score=score,
            )
        )
    return articles


def _parse_algolia_json(payload: str, source: Source) -> list[TechArticle]:
    data = json.loads(payload)
    articles: list[TechArticle] = []
    for hit in data.get("hits", []):
        title = (hit.get("title") or hit.get("story_title") or "").strip()
        url = (hit.get("url") or hit.get("story_url") or "").strip()
        if not title:
            continue
        created_at = hit.get("created_at") or hit.get("created_at_i")
        if isinstance(created_at, (int, float)):
            published_at = _unix_to_iso(int(created_at))
        else:
            published_at = str(created_at or "")
        points = hit.get("points") or hit.get("story_points")
        articles.append(
            TechArticle(
                title=title,
                url=url or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                summary=(hit.get("comment_text") or hit.get("_tags", [""])[0] if hit.get("_tags") else "")[:200],
                published_at=published_at,
                topics=["ai", "hacker-news"],
                source=source.name,
                source_id=source.id,
                author=(hit.get("author") or "").strip(),
                score=int(points) if points is not None else None,
            )
        )
    return articles


def _unix_to_iso(timestamp: int | None) -> str:
    if not timestamp:
        return ""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
