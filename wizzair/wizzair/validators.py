from __future__ import annotations

import re

from wizzair.models import Destination

FLIGHT_CODE_RE = re.compile(r"\bW6\d+\b")
PRICE_RE = re.compile(r"zł\s*[\d.,]+", re.IGNORECASE)
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b")
NO_RESULTS_SNIPPET = "niestety, nie znaleziono żadnych wyników"


def destination_names(destination: Destination) -> set[str]:
    names = {destination.code.upper()}
    label = destination.label.split("(")[0].strip()
    if label:
        names.add(label.upper())
    return names


def card_matches_route(
    text: str,
    *,
    destination: Destination,
    require_price: bool = True,
) -> bool:
    if not text or len(text) < 80 or len(text) > 1200:
        return False

    upper = text.upper()
    if "WYBIERZ" not in upper:
        return False
    if not FLIGHT_CODE_RE.search(text):
        return False

    names = destination_names(destination)
    if not any(name in upper for name in names):
        return False

    times = TIME_RE.findall(text)
    if len(times) < 2:
        return False

    if require_price and not PRICE_RE.search(text):
        return False

    return True


def page_has_no_results(text: str) -> bool:
    return NO_RESULTS_SNIPPET in text.lower()
