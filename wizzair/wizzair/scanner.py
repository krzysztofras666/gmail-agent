from __future__ import annotations

from datetime import date, timedelta

from playwright.async_api import async_playwright
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeElapsedColumn

from wizzair.browser import open_browser_context, persist_session
from wizzair.config import Settings
from wizzair.destinations_cache import load_cached_destinations, save_cached_destinations
from wizzair.models import Destination, MultipassFlight, ScanDiagnostic, ScanResult
from wizzair.multipass import discover_destinations, login
from wizzair.ui_search import search_route_ui


async def scan_multipass(settings: Settings) -> ScanResult:
    dates = _search_dates(settings.days_ahead)
    flights: list[MultipassFlight] = []
    diagnostics: list[ScanDiagnostic] = []
    console = Console(stderr=True)

    async with async_playwright() as playwright:
        browser, context = await open_browser_context(playwright, settings)
        page = await login(context, settings)
        session_path = await persist_session(context, settings)
        console.print(f"[dim]Sesja zapisana: {session_path}[/dim]")

        destinations_by_origin: dict[str, list[Destination]] = {}
        for origin in settings.origins:
            cached = load_cached_destinations(origin)
            if cached is not None:
                console.print(f"[dim]Destynacje {origin} z cache ({len(cached)})[/dim]")
                destinations_by_origin[origin] = _filter_destinations(cached, settings)
            else:
                console.print(f"[cyan]Pobieram destynacje dla {origin}...[/cyan]")
                discovered = await discover_destinations(page, origin)
                save_cached_destinations(origin, discovered)
                destinations_by_origin[origin] = _filter_destinations(discovered, settings)

        jobs: list[tuple[str, Destination, str]] = []
        for origin, destinations in destinations_by_origin.items():
            for destination in destinations:
                for departure_date in dates:
                    jobs.append((origin, destination, departure_date))

        console.print(
            f"[dim]Skan: {len(settings.origins)} lotnisk × "
            f"{sum(len(items) for items in destinations_by_origin.values())} destynacji × "
            f"{len(dates)} dni = {len(jobs)} wyszukiwań[/dim]"
        )

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Skanowanie lotów w UI Multipass", total=len(jobs))

            for origin, destination, departure_date in jobs:
                progress.update(
                    task,
                    description=f"{origin}→{destination.code} {departure_date}",
                )
                try:
                    found = await search_route_ui(
                        page,
                        origin=origin,
                        destination=destination,
                        departure_date=departure_date,
                        settings=settings,
                    )
                    diagnostics.append(
                        ScanDiagnostic(
                            origin=origin,
                            destination=destination.code,
                            departure_date=departure_date,
                            flights_found=len(found),
                        )
                    )
                    flights.extend(found)
                except Exception as exc:  # noqa: BLE001
                    diagnostics.append(
                        ScanDiagnostic(
                            origin=origin,
                            destination=destination.code,
                            departure_date=departure_date,
                            flights_found=0,
                            error=str(exc),
                        )
                    )
                progress.advance(task)

        await browser.close()

    flights.sort(
        key=lambda flight: (
            flight.departure_date,
            flight.origin,
            flight.destination,
            flight.departure_time,
        )
    )
    return ScanResult(flights=flights, diagnostics=diagnostics)


async def login_and_save_session(settings: Settings) -> str:
    async with async_playwright() as playwright:
        browser, context = await open_browser_context(playwright, settings)
        page = await login(context, settings)
        session_path = await persist_session(context, settings)
        await browser.close()
        return str(session_path)


def _filter_destinations(destinations: list[Destination], settings: Settings) -> list[Destination]:
    if not settings.destination_filter:
        return destinations
    allowed = set(settings.destination_filter)
    return [dest for dest in destinations if dest.code in allowed]


def _search_dates(days_ahead: int) -> list[str]:
    start = date.today()
    return [(start + timedelta(days=offset)).isoformat() for offset in range(days_ahead)]
