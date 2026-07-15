from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from travel_agent.models import RunResult, SiteDiagnostic, TravelOffer


def print_run_result(result: RunResult, *, show_diagnostics: bool = True) -> None:
    console = Console()
    table = Table(title="Travel deals")
    table.add_column("Destination")
    table.add_column("Dates")
    table.add_column("Price", justify="right")
    table.add_column("Source")

    for offer in result.offers:
        table.add_row(
            offer.destination,
            _format_dates(offer),
            _format_price(offer),
            offer.source,
        )

    if result.offers:
        console.print(table)
    else:
        console.print("[yellow]No offers found.[/yellow]")

    if show_diagnostics and result.diagnostics:
        diag = Table(title="Diagnostics")
        diag.add_column("Site")
        diag.add_column("Engine")
        diag.add_column("Chars", justify="right")
        diag.add_column("Offers", justify="right")
        diag.add_column("Error")
        for row in result.diagnostics:
            diag.add_row(
                row.site_name,
                row.engine,
                str(row.chars_fetched),
                str(row.offers_extracted),
                row.error,
            )
        console.print(diag)


def print_json(result: RunResult) -> None:
    payload = {
        "offers": [_offer_to_dict(offer) for offer in result.offers],
        "diagnostics": [
            {
                "site_id": row.site_id,
                "site_name": row.site_name,
                "engine": row.engine,
                "chars_fetched": row.chars_fetched,
                "offers_extracted": row.offers_extracted,
                "error": row.error,
            }
            for row in result.diagnostics
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _offer_to_dict(offer: TravelOffer) -> dict:
    return {
        "destination": offer.destination,
        "departure_date": offer.departure_date,
        "return_date": offer.return_date,
        "price": offer.price,
        "currency": offer.currency,
        "nights": offer.nights,
        "title": offer.title,
        "notes": offer.notes,
        "source": offer.source,
        "source_id": offer.source_id,
        "url": offer.url,
    }


def _format_dates(offer: TravelOffer) -> str:
    if offer.return_date:
        return f"{offer.departure_date} → {offer.return_date}"
    return offer.departure_date


def _format_price(offer: TravelOffer) -> str:
    amount = f"{offer.price:,.0f}".replace(",", " ")
    return f"{amount} {offer.currency}"
