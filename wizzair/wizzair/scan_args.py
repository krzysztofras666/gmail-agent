from __future__ import annotations

import argparse
from dataclasses import replace

from wizzair.config import Settings


def add_scan_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--origin",
        action="append",
        dest="origins",
        help="Lotnisko wylotu (np. KRK). Można podać wielokrotnie.",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Ile dni do przodu skanować (domyślnie z .env, zwykle 4).",
    )
    parser.add_argument(
        "--destination",
        action="append",
        dest="destinations",
        help="Filtruj destynacje po kodzie IATA (np. FCO). Można podać wielokrotnie.",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Krótsze timeouty UI (szybciej, minimalnie mniej stabilnie).",
    )


def apply_scan_args(settings: Settings, args: argparse.Namespace) -> Settings:
    origins = _normalize_csv_values(getattr(args, "origins", None))
    destinations = _normalize_csv_values(getattr(args, "destinations", None))
    days = getattr(args, "days", None)
    fast = getattr(args, "fast", False)

    updates: dict = {}
    if origins:
        updates["origins"] = tuple(origins)
    if destinations:
        updates["destination_filter"] = tuple(destinations)
    if days is not None:
        updates["days_ahead"] = max(1, days)
    if fast:
        updates["fast_scan"] = True
    return replace(settings, **updates) if updates else settings


def _normalize_csv_values(values: list[str] | None) -> list[str]:
    if not values:
        return []
    normalized: list[str] = []
    for value in values:
        normalized.extend(part.strip().upper() for part in value.split(",") if part.strip())
    return normalized
