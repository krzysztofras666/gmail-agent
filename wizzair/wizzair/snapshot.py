from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from wizzair.models import MultipassFlight, ScanResult


@dataclass
class ScanDelta:
    added: list[MultipassFlight] = field(default_factory=list)
    removed: list[MultipassFlight] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed)


def flight_key(flight: MultipassFlight) -> str:
    return "|".join(
        [
            flight.origin.upper(),
            flight.destination.upper(),
            flight.departure_date,
            flight.flight_code,
            flight.departure_time,
        ]
    )


def compare_flights(baseline: list[MultipassFlight], current: list[MultipassFlight]) -> ScanDelta:
    baseline_map = {flight_key(flight): flight for flight in baseline}
    current_map = {flight_key(flight): flight for flight in current}

    added = [current_map[key] for key in current_map.keys() - baseline_map.keys()]
    removed = [baseline_map[key] for key in baseline_map.keys() - current_map.keys()]

    added.sort(key=_sort_key)
    removed.sort(key=_sort_key)
    return ScanDelta(added=added, removed=removed)


def morning_snapshot_path(*, root: Path | None = None, day: date | None = None) -> Path:
    root = root or Path("logs")
    day = day or date.today()
    return root / "snapshots" / f"{day.isoformat()}-morning.json"


def save_morning_snapshot(result: ScanResult, *, root: Path | None = None) -> Path:
    path = morning_snapshot_path(root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": date.today().isoformat(),
        "slot": "morning",
        "flights": [_flight_to_dict(flight) for flight in result.flights],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_morning_snapshot(*, root: Path | None = None, day: date | None = None) -> list[MultipassFlight]:
    path = morning_snapshot_path(root=root, day=day)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [_flight_from_dict(item) for item in payload.get("flights", [])]


def _sort_key(flight: MultipassFlight) -> tuple:
    return (flight.departure_date, flight.origin, flight.destination, flight.departure_time)


def _flight_to_dict(flight: MultipassFlight) -> dict:
    return asdict(flight)


def _flight_from_dict(data: dict) -> MultipassFlight:
    return MultipassFlight(**data)
