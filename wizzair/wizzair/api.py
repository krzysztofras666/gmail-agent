from __future__ import annotations

import re
from typing import Any

from wizzair.models import MultipassFlight

PASS_ID_RE = re.compile(r"pass_id['\"]:\s*['\"]([^'\"]+)['\"]")


def availability_api_url(pass_id: str) -> str:
    return (
        "https://multipass.wizzair.com/pl/w6/subscriptions/json/availability/"
        f"{pass_id}"
    )


def build_availability_payload(
    *,
    origin: str,
    destination: str,
    departure_date: str,
) -> dict[str, Any]:
    return {
        "flightType": "OW",
        "origin": origin.upper(),
        "destination": destination.upper(),
        "departure": departure_date,
        "arrival": "",
        "intervalSubtype": None,
    }


def parse_availability_response(
    data: dict[str, Any],
    *,
    origin: str,
    destination: str,
    departure_date: str,
) -> list[MultipassFlight]:
    flights: list[MultipassFlight] = []
    for leg in data.get("flightsOutbound") or []:
        flights.append(
            MultipassFlight(
                origin=leg.get("departureStationCode", origin).upper(),
                origin_name=leg.get("departureStationText", origin),
                destination=leg.get("arrivalStationCode", destination).upper(),
                destination_name=leg.get("arrivalStationText", destination),
                departure_date=leg.get("departureDateIso") or departure_date,
                departure_time=leg.get("departure", ""),
                arrival_time=leg.get("arrival", ""),
                flight_code=leg.get("flightCode", ""),
                duration=leg.get("duration", ""),
                price=float(leg.get("displayPrice") or leg.get("price") or 0),
                currency=leg.get("currency", ""),
                stops=leg.get("stops", ""),
            )
        )
    return flights


def extract_pass_id(html: str) -> str | None:
    match = PASS_ID_RE.search(html)
    return match.group(1) if match else None
