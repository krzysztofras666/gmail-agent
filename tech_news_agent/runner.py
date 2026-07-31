from __future__ import annotations

import asyncio

from tech_news_agent.aggregate import aggregate_articles
from tech_news_agent.clean import clean_content
from tech_news_agent.config import Settings
from tech_news_agent.extract import extract_articles
from tech_news_agent.fetch import fetch_algolia_articles, fetch_hn_articles, fetch_source
from tech_news_agent.models import RunResult, SourceDiagnostic, TechArticle
from tech_news_agent.sources import Source, get_sources


async def run_agent(
    settings: Settings,
    *,
    source_ids: list[str] | None = None,
    max_articles: int | None = None,
) -> RunResult:
    sources = get_sources(source_ids)
    limit = max_articles or settings.max_articles
    semaphore = asyncio.Semaphore(settings.fetch_concurrency)

    async def process_source(source: Source) -> tuple[list[TechArticle], SourceDiagnostic]:
        async with semaphore:
            try:
                if source.kind == "hn_api":
                    articles = await fetch_hn_articles(settings, source)
                    return articles, SourceDiagnostic(
                        source_id=source.id,
                        source_name=source.name,
                        engine="api",
                        chars_fetched=len(articles),
                        articles_extracted=len(articles),
                    )

                if source.id == "hn_algolia":
                    articles = await fetch_algolia_articles(settings, source)
                    return articles, SourceDiagnostic(
                        source_id=source.id,
                        source_name=source.name,
                        engine="api",
                        chars_fetched=len(articles),
                        articles_extracted=len(articles),
                    )

                fetch_result = await fetch_source(settings, source)
                if fetch_result.error and not fetch_result.text:
                    return [], SourceDiagnostic(
                        source_id=source.id,
                        source_name=source.name,
                        engine=fetch_result.engine,
                        chars_fetched=0,
                        articles_extracted=0,
                        error=fetch_result.error,
                    )

                cleaned = clean_content(
                    fetch_result.text,
                    kind=source.kind,
                    max_chars=settings.max_text_chars,
                )
                articles = extract_articles(settings, source, cleaned)
                return articles, SourceDiagnostic(
                    source_id=source.id,
                    source_name=source.name,
                    engine=fetch_result.engine,
                    chars_fetched=len(cleaned),
                    articles_extracted=len(articles),
                    error=fetch_result.error,
                )
            except Exception as exc:  # noqa: BLE001
                return [], SourceDiagnostic(
                    source_id=source.id,
                    source_name=source.name,
                    engine="skipped",
                    chars_fetched=0,
                    articles_extracted=0,
                    error=str(exc),
                )

    pairs = await asyncio.gather(*(process_source(source) for source in sources))

    all_articles: list[TechArticle] = []
    diagnostics: list[SourceDiagnostic] = []
    for articles, diag in pairs:
        all_articles.extend(articles)
        diagnostics.append(diag)

    aggregated = aggregate_articles(
        all_articles,
        max_articles=limit,
        max_per_topic=settings.max_per_topic,
        hours_lookback=settings.hours_lookback,
    )
    return RunResult(articles=aggregated, diagnostics=diagnostics)
