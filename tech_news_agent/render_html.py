from __future__ import annotations

from datetime import date
from html import escape

from tech_news_agent.models import RunResult, TechArticle


def build_subject(result: RunResult) -> str:
    sources = {article.source for article in result.articles}
    today = date.today().isoformat()
    return (
        f"Tech News — {today} "
        f"({len(result.articles)} articles, {len(sources)} sources)"
    )


def render_html(result: RunResult) -> str:
    sections = "\n".join(_render_article(article) for article in result.articles)
    if not sections:
        sections = "<p>No articles found in this run.</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(build_subject(result))}</title>
</head>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.5; max-width: 720px;">
  <h2 style="margin: 0 0 8px;">Tech News Digest</h2>
  <p style="margin: 0 0 20px; color: #555;">Curated headlines from configured tech sources.</p>
  {sections}
</body>
</html>"""


def render_plain_text(result: RunResult) -> str:
    lines = [build_subject(result), ""]
    for article in result.articles:
        lines.append(f"- {article.title}")
        if article.summary:
            lines.append(f"  {article.summary}")
        if article.url:
            lines.append(f"  {article.url}")
        meta = " | ".join(
            part
            for part in (
                article.source,
                article.published_at,
                ", ".join(article.topics[:3]),
                f"score {article.score}" if article.score is not None else "",
            )
            if part
        )
        if meta:
            lines.append(f"  ({meta})")
        lines.append("")
    if not result.articles:
        lines.append("No articles found in this run.")
    return "\n".join(lines).rstrip() + "\n"


def _render_article(article: TechArticle) -> str:
    title = escape(article.title)
    if article.url:
        title = f'<a href="{escape(article.url)}" style="color: #1a56db; text-decoration: none;">{title}</a>'
    topics = ", ".join(escape(topic) for topic in article.topics[:3])
    meta_parts = [escape(article.source)]
    if article.published_at:
        meta_parts.append(escape(article.published_at))
    if article.score is not None:
        meta_parts.append(f"score {article.score}")
    meta = " · ".join(meta_parts)
    summary = f'<p style="margin: 6px 0 0; color: #444;">{escape(article.summary)}</p>' if article.summary else ""
    topics_line = (
        f'<div style="margin-top: 6px; color: #777; font-size: 12px;">{topics}</div>'
        if topics
        else ""
    )
    return f"""
  <div style="margin: 0 0 18px; padding-bottom: 18px; border-bottom: 1px solid #eee;">
    <div style="font-size: 16px; font-weight: bold;">{title}</div>
    <div style="margin-top: 4px; color: #777; font-size: 12px;">{meta}</div>
    {summary}
    {topics_line}
  </div>"""
