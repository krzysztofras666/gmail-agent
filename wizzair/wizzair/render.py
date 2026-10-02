from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from wizzair.models import MultipassFlight, ScanDiagnostic, ScanResult


def print_scan_result(result: ScanResult, *, show_diagnostics: bool = False) -> None:
    console = Console()
    table = Table(title="Dostępne loty Wizz Multipass (All You Can Fly)")
    table.add_column("Data")
    table.add_column("Trasa")
    table.add_column("Lot")
    table.add_column("Godziny")
    table.add_column("Czas")
    table.add_column("Cena", justify="right")

    for flight in result.flights:
        table.add_row(
            flight.departure_date,
            f"{flight.origin_name} ({flight.origin}) → {flight.destination_name} ({flight.destination})",
            flight.flight_code,
            f"{flight.departure_time} → {flight.arrival_time}",
            flight.duration,
            _format_price(flight),
        )

    if result.flights:
        console.print(table)
        console.print(f"\nZnaleziono [green]{len(result.flights)}[/green] lot(ów).")
    else:
        console.print("[yellow]Brak dostępnych lotów w wybranym zakresie dat.[/yellow]")

    if show_diagnostics and result.diagnostics:
        diag = Table(title="Diagnostyka")
        diag.add_column("Skąd")
        diag.add_column("Dokąd")
        diag.add_column("Data")
        diag.add_column("Loty", justify="right")
        diag.add_column("Błąd")
        for row in result.diagnostics:
            if row.flights_found or row.error:
                diag.add_row(
                    row.origin,
                    row.destination,
                    row.departure_date,
                    str(row.flights_found),
                    row.error,
                )
        console.print(diag)


def print_json(result: ScanResult) -> None:
    payload = {
        "flights": [_flight_to_dict(flight) for flight in result.flights],
        "diagnostics": [_diag_to_dict(row) for row in result.diagnostics],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _flight_to_dict(flight: MultipassFlight) -> dict:
    return {
        "origin": flight.origin,
        "origin_name": flight.origin_name,
        "destination": flight.destination,
        "destination_name": flight.destination_name,
        "departure_date": flight.departure_date,
        "departure_time": flight.departure_time,
        "arrival_time": flight.arrival_time,
        "flight_code": flight.flight_code,
        "duration": flight.duration,
        "price": flight.price,
        "currency": flight.currency,
        "stops": flight.stops,
        "multipass_url": flight.multipass_url,
        "wizzair_url": flight.wizzair_url,
    }


def _diag_to_dict(row: ScanDiagnostic) -> dict:
    return {
        "origin": row.origin,
        "destination": row.destination,
        "departure_date": row.departure_date,
        "flights_found": row.flights_found,
        "error": row.error,
    }


def _format_price(flight: MultipassFlight) -> str:
    amount = f"{flight.price:,.2f}".replace(",", " ")
    return f"{amount} {flight.currency}"
