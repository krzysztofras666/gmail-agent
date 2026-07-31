from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    urls: tuple[str, ...] = ()
    kind: Literal["rss", "html", "hn_api"] = "rss"


SOURCES: tuple[Source, ...] = (
    Source(
        id="hn",
        name="Hacker News",
        kind="hn_api",
    ),
    Source(
        id="techcrunch",
        name="TechCrunch",
        urls=("https://techcrunch.com/feed/",),
        kind="rss",
    ),
    Source(
        id="arstechnica",
        name="Ars Technica",
        urls=("https://feeds.arstechnica.com/arstechnica/index",),
        kind="rss",
    ),
    Source(
        id="theverge",
        name="The Verge",
        urls=("https://www.theverge.com/rss/index.xml",),
        kind="rss",
    ),
    Source(
        id="lobsters",
        name="Lobsters",
        urls=("https://lobste.rs/rss",),
        kind="rss",
    ),
    Source(
        id="github_blog",
        name="GitHub Blog",
        urls=("https://github.blog/feed/",),
        kind="rss",
    ),
    Source(
        id="hn_algolia",
        name="HN — AI/ML",
        urls=(
            "https://hn.algolia.com/api/v1/search?tags=front_page&query=AI&hitsPerPage=20",
        ),
        kind="html",
    ),
)

_SOURCE_BY_ID = {source.id: source for source in SOURCES}


def get_sources(source_ids: list[str] | None = None) -> list[Source]:
    if not source_ids:
        return list(SOURCES)
    unknown = [source_id for source_id in source_ids if source_id not in _SOURCE_BY_ID]
    if unknown:
        raise ValueError(f"Unknown source id(s): {', '.join(unknown)}")
    return [_SOURCE_BY_ID[source_id] for source_id in source_ids]
