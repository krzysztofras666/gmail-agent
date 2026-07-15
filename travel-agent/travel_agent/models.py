from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class TravelOffer:
    destination: str
    departure_date: str
    return_date: str
    price: float
    currency: str
    nights: int | None
    title: str
    notes: str
    source: str
    source_id: str
    url: str = ""


@dataclass
class SiteDiagnostic:
    site_id: str
    site_name: str
    engine: Literal["http", "browser", "skipped"]
    chars_fetched: int
    offers_extracted: int
    error: str = ""


@dataclass
class FetchResult:
    site_id: str
    text: str
    engine: Literal["http", "browser"]
    url: str
    error: str = ""


@dataclass
class RunResult:
    offers: list[TravelOffer] = field(default_factory=list)
    diagnostics: list[SiteDiagnostic] = field(default_factory=list)
