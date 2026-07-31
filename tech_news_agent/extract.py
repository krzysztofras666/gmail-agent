from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from tech_news_agent.config import Settings
from tech_news_agent.models import TechArticle
from tech_news_agent.sources import Source

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "articles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "summary": {"type": "string"},
                    "published_at": {"type": "string"},
                    "topics": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "author": {"type": "string"},
                    "score": {"type": ["integer", "null"]},
                },
                "required": ["title", "url", "summary", "published_at", "topics"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["articles"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You extract tech news articles from messy feed or page text.
Return only valid JSON matching the schema.
Rules:
- Skip navigation, ads, newsletter signups, and generic site chrome.
- Never invent facts, URLs, or dates that are not present in the text.
- summary should be 1-2 concise sentences describing why the article matters.
- published_at should be ISO 8601 (YYYY-MM-DD or full datetime) when possible.
- topics should be 1-3 lowercase tags like ai, security, startup, hardware, open-source.
- If no real articles are present, return {"articles": []}.
"""


def extract_articles(
    settings: Settings,
    source: Source,
    cleaned_text: str,
) -> list[TechArticle]:
    if not cleaned_text.strip():
        return []

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "tech_articles",
                "strict": True,
                "schema": EXTRACTION_SCHEMA,
            },
        },
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Source: {source.name}\n"
                    f"Source id: {source.id}\n\n"
                    f"Text:\n{cleaned_text}"
                ),
            },
        ],
        temperature=0,
    )
    content = response.choices[0].message.content or "{}"
    payload = json.loads(content)
    return [_to_article(item, source) for item in payload.get("articles", [])]


def _to_article(item: dict[str, Any], source: Source) -> TechArticle:
    topics = [topic.strip().lower() for topic in item.get("topics", []) if topic.strip()]
    return TechArticle(
        title=item["title"].strip(),
        url=item.get("url", "").strip(),
        summary=item.get("summary", "").strip(),
        published_at=item.get("published_at", "").strip(),
        topics=topics or ["general"],
        source=source.name,
        source_id=source.id,
        author=item.get("author", "").strip(),
        score=item.get("score"),
    )
