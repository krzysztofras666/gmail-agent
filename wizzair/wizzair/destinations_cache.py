from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from wizzair.config import default_session_path
from wizzair.models import Destination


def destinations_cache_path(origin: str) -> Path:
    return default_session_path().parent / f"destinations-{origin.upper()}.json"


def load_cached_destinations(origin: str, *, max_age_days: int = 7) -> list[Destination] | None:
    path = destinations_cache_path(origin)
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    cached_on = payload.get("cached_on")
    items = payload.get("destinations")
    if not cached_on or not isinstance(items, list):
        return None

    age_days = (date.today() - date.fromisoformat(cached_on)).days
    if age_days > max_age_days:
        return None

    destinations: list[Destination] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code", "")).strip().upper()
        label = str(item.get("label", "")).strip()
        if code and label:
            destinations.append(Destination(code=code, label=label))
    return destinations or None


def save_cached_destinations(origin: str, destinations: list[Destination]) -> Path:
    path = destinations_cache_path(origin)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "cached_on": date.today().isoformat(),
        "origin": origin.upper(),
        "destinations": [{"code": dest.code, "label": dest.label} for dest in destinations],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
