from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from tech_news_agent.models import RunResult, SourceDiagnostic, TechArticle


def print_run_result(result: RunResult, *, show_diagnostics: bool = True) -> None:
    console = Console()
    table = Table(title="Tech news digest")
    table.add_column("Title", max_width=50)
    table.add_column("Source")
    table.add_column("Published")
    table.add_column("Topics")
    table.add_column("Score", justify="right")

    for article in result.articles:
        table.add_row(
            article.title,
            article.source,
            article.published_at or "—",
            ", ".join(article.topics[:3]),
            str(article.score) if article.score is not None else "—",
        )

    if result.articles:
        console.print(table)
    else:
        console.print("[yellow]No articles found.[/yellow]")

    if show_diagnostics and result.diagnostics:
        diag = Table(title="Diagnostics")
        diag.add_column("Source")
        diag.add_column("Engine")
        diag.add_column("Chars", justify="right")
        diag.add_column("Articles", justify="right")
        diag.add_column("Error")
        for row in result.diagnostics:
            diag.add_row(
                row.source_name,
                row.engine,
                str(row.chars_fetched),
                str(row.articles_extracted),
                row.error,
            )
        console.print(diag)


def print_json(result: RunResult) -> None:
    payload = {
        "articles": [_article_to_dict(article) for article in result.articles],
        "diagnostics": [
            {
                "source_id": row.source_id,
                "source_name": row.source_name,
                "engine": row.engine,
                "chars_fetched": row.chars_fetched,
                "articles_extracted": row.articles_extracted,
                "error": row.error,
            }
            for row in result.diagnostics
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _article_to_dict(article: TechArticle) -> dict:
    return {
        "title": article.title,
        "url": article.url,
        "summary": article.summary,
        "published_at": article.published_at,
        "topics": article.topics,
        "source": article.source,
        "source_id": article.source_id,
        "author": article.author,
        "score": article.score,
    }
