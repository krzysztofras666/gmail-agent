from __future__ import annotations

from dataclasses import dataclass, field


NO_RESULTS_SNIPPET = "Niestety, nie znaleziono żadnych wyników"


@dataclass(frozen=True)
class Destination:
    code: str
    label: str


@dataclass
class MultipassFlight:
    origin: str
    origin_name: str
    destination: str
    destination_name: str
    departure_date: str
    departure_time: str
    arrival_time: str
    flight_code: str
    duration: str
    price: float
    currency: str
    stops: str = ""
    multipass_url: str = ""
    wizzair_url: str = ""


@dataclass
class ScanDiagnostic:
    origin: str
    destination: str
    departure_date: str
    flights_found: int
    error: str = ""


@dataclass
class ScanResult:
    flights: list[MultipassFlight] = field(default_factory=list)
    diagnostics: list[ScanDiagnostic] = field(default_factory=list)
