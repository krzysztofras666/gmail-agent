from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class TechArticle:
    title: str
    url: str
    summary: str
    published_at: str
    topics: list[str]
    source: str
    source_id: str
    author: str = ""
    score: int | None = None


@dataclass
class SourceDiagnostic:
    source_id: str
    source_name: str
    engine: Literal["http", "api", "skipped"]
    chars_fetched: int
    articles_extracted: int
    error: str = ""


@dataclass
class FetchResult:
    source_id: str
    text: str
    engine: Literal["http", "api"]
    url: str
    error: str = ""


@dataclass
class RunResult:
    articles: list[TechArticle] = field(default_factory=list)
    diagnostics: list[SourceDiagnostic] = field(default_factory=list)
