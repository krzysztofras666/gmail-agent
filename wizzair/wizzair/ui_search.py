from __future__ import annotations

import re
from datetime import date
from urllib.parse import parse_qs, urlparse

from playwright.async_api import Page

from wizzair.config import WALLETS_URL, Settings
from wizzair.models import Destination, MultipassFlight
from wizzair.multipass import ORIGIN_QUERIES, dismiss_modals
from wizzair.urls import multipass_wallets_url, wizzair_booking_url
from wizzair.validators import (
    FLIGHT_CODE_RE,
    card_matches_route,
    destination_names,
    page_has_no_results,
)

TIME_LINE_RE = re.compile(r"^\d{1,2}:\d{2}$")
DURATION_RE = re.compile(r"^\d+h \d+m$")


async def search_route_ui(
    page: Page,
    *,
    origin: str,
    destination: Destination,
    departure_date: str,
    settings: Settings | None = None,
) -> list[MultipassFlight]:
    fast = settings.fast_scan if settings is not None else False
    origin_code = origin.upper()
    dest_code = destination.code.upper()
    origin_query, origin_pick = ORIGIN_QUERIES.get(origin_code, (origin_code[:3], origin_code))
    dest_query = _destination_query(destination.label)
    dest_pick = _pick_label(destination.label)

    await page.goto(WALLETS_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(_ms(1000, fast))
    await dismiss_modals(page)

    await _select_autocomplete(
        page,
        field="origin",
        query=origin_query,
        pick=origin_pick,
        fast=fast,
    )
    await _select_autocomplete(
        page,
        field="destination",
        query=dest_query,
        pick=dest_pick,
        iata_code=dest_code,
        fast=fast,
    )
    if not await _verify_selected_destination(page, destination):
        return []

    if not await _select_departure_date(page, departure_date, fast=fast):
        return []

    search_button = page.locator("button.SearchCombo-submit")
    if not await search_button.is_enabled():
        return []

    previous_url = page.url
    await search_button.click()
    if not await _wait_for_results_page(
        page,
        origin=origin_code,
        destination=dest_code,
        departure_date=departure_date,
        previous_url=previous_url,
        fast=fast,
    ):
        return []

    body_text = await page.evaluate("() => document.body.innerText")
    if page_has_no_results(body_text):
        return []

    raw_cards = await _extract_result_cards(page, destination=destination)
    flights: list[MultipassFlight] = []
    seen: set[str] = set()
    multipass_url = page.url if "availability" in page.url else multipass_wallets_url()
    wizzair_url = wizzair_booking_url(
        origin=origin_code,
        destination=dest_code,
        departure_date=departure_date,
    )
    for card_text in raw_cards:
        if not card_matches_route(card_text, destination=destination):
            continue
        parsed = _parse_card_text(
            card_text,
            origin=origin_code,
            destination=dest_code,
            departure_date=departure_date,
            destination_label=destination.label,
            multipass_url=multipass_url,
            wizzair_url=wizzair_url,
        )
        if parsed is None:
            continue
        key = f"{parsed.flight_code}|{parsed.departure_date}|{parsed.departure_time}"
        if key in seen:
            continue
        seen.add(key)
        flights.append(parsed)

    return flights


async def _extract_result_cards(page: Page, *, destination: Destination) -> list[str]:
    dest_names = sorted(destination_names(destination))
    return await page.evaluate(
        """({ destNames }) => {
            const cards = [...document.querySelectorAll('[class*="SearchResult"]')];
            return cards
                .map((card) => {
                    const text = (card.innerText || '').trim();
                    const button = [...card.querySelectorAll('button')].find((node) =>
                        /WYBIERZ/i.test(node.innerText || '')
                    );
                    if (!button) return '';
                    const upper = text.toUpperCase();
                    const hasDestination = destNames.some((name) => upper.includes(name));
                    if (!hasDestination) return '';
                    if (!/W6\\d+/.test(text)) return '';
                    if (!/zł\\s*[\\d.,]+/i.test(text)) return '';
                    if (text.length < 80 || text.length > 1200) return '';
                    return text;
                })
                .filter(Boolean);
        }""",
        {"destNames": dest_names},
    )


async def _wait_for_results_page(
    page: Page,
    *,
    origin: str,
    destination: str,
    departure_date: str,
    previous_url: str,
    fast: bool,
) -> bool:
    timeout = _ms(20000, fast)
    try:
        await page.wait_for_url("**/availability/**", timeout=timeout)
    except Exception:
        await page.wait_for_timeout(_ms(3000, fast))

    try:
        await page.wait_for_function(
            """([origin, destination, departureDate, previousUrl]) => {
                const href = window.location.href.toUpperCase();
                const changed = window.location.href !== previousUrl;
                const urlMatches =
                    href.includes(origin) &&
                    href.includes(destination) &&
                    href.includes(departureDate);
                const text = document.body.innerText.toLowerCase();
                const noResults = text.includes('niestety, nie znaleziono żadnych wyników');
                const hasCards = [...document.querySelectorAll('[class*="SearchResult"]')].some((card) => {
                    const body = (card.innerText || '').toUpperCase();
                    return body.includes(destination) && /W6\\d+/.test(body) && /WYBIERZ/i.test(body);
                });
                return changed && (urlMatches || noResults || hasCards);
            }""",
            arg=[origin, destination, departure_date, previous_url],
            timeout=timeout,
        )
    except Exception:
        return _url_matches_search(page.url, origin=origin, destination=destination, departure_date=departure_date)

    await page.wait_for_timeout(_ms(700, fast))
    return True


def _url_matches_search(url: str, *, origin: str, destination: str, departure_date: str) -> bool:
    upper = url.upper()
    if origin in upper and destination in upper and departure_date in upper:
        return True

    query = parse_qs(urlparse(url).query)
    values = {key.lower(): [item.upper() for item in items] for key, items in query.items()}
    origin_ok = origin in values.get("origin", []) or origin in upper
    destination_ok = destination in values.get("destination", []) or destination in upper
    date_ok = departure_date in values.get("departure", []) or departure_date in upper
    return origin_ok and destination_ok and date_ok


async def _verify_selected_destination(page: Page, destination: Destination) -> bool:
    value = await page.locator('input[id^="autocomplete-destination"]').first.input_value()
    upper = value.upper()
    names = destination_names(destination)
    return any(name in upper for name in names)


async def _select_autocomplete(
    page: Page,
    *,
    field: str,
    query: str,
    pick: str,
    iata_code: str | None = None,
    fast: bool,
) -> None:
    field_input = page.locator(f'input[id^="autocomplete-{field}"]').first
    await field_input.click()
    await field_input.fill("")
    await field_input.type(query, delay=20 if fast else 30)
    await page.wait_for_timeout(_ms(900, fast))

    options = page.locator("ul.autocomplete-result-list:visible li")
    if iata_code:
        exact = options.filter(has_text=re.compile(rf"\({re.escape(iata_code)}\)", re.IGNORECASE))
        if await exact.count() > 0:
            await exact.first.click()
        else:
            await options.filter(has_text=pick).first.click()
    else:
        await options.filter(has_text=pick).first.click()
    await page.wait_for_timeout(_ms(400, fast))


async def _select_departure_date(page: Page, departure_date: str, *, fast: bool) -> bool:
    departure_input = page.locator("#Odloty").first
    await departure_input.click()
    await page.wait_for_timeout(_ms(600, fast))

    for _ in range(8):
        cell = page.locator(f'td.cell[title="{departure_date}"]:not(.disabled)')
        if await cell.count() > 0:
            await cell.first.click()
            await page.wait_for_timeout(_ms(400, fast))
            return True
        await page.locator(".Datepicker-btn-icon-right").first.click()
        await page.wait_for_timeout(_ms(300, fast))

    return False


def _ms(value: int, fast: bool) -> int:
    if not fast:
        return value
    return max(200, int(value * 0.6))


def _destination_query(label: str) -> str:
    name = _pick_label(label)
    return name[:4] if len(name) >= 4 else name


def _pick_label(label: str) -> str:
    return label.split("(")[0].strip()


def _parse_card_text(
    text: str,
    *,
    origin: str,
    destination: str,
    departure_date: str,
    destination_label: str,
    multipass_url: str,
    wizzair_url: str,
) -> MultipassFlight | None:
    if not card_matches_route(text, destination=Destination(code=destination, label=destination_label)):
        return None

    code_match = FLIGHT_CODE_RE.search(text)
    if not code_match:
        return None

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    times = [line for line in lines if TIME_LINE_RE.fullmatch(line)]
    if len(times) < 2:
        return None

    duration = next((line for line in lines if DURATION_RE.fullmatch(line)), "")
    origin_name = next(
        (
            line
            for line in lines
            if line not in times
            and "UTC" not in line
            and "W6" not in line
            and "zł" not in line.lower()
            and "WYBIERZ" not in line.upper()
        ),
        origin,
    )
    destination_name = destination_label.split("(")[0].strip()
    price_match = re.search(r"zł\s*([\d.,]+)", text, re.IGNORECASE)
    price = float(price_match.group(1).replace(",", ".")) if price_match else 0.0
    currency = "PLN" if price_match else ""

    return MultipassFlight(
        origin=origin,
        origin_name=origin_name,
        destination=destination,
        destination_name=destination_name,
        departure_date=departure_date,
        departure_time=times[0],
        arrival_time=times[1],
        flight_code=code_match.group(0),
        duration=duration,
        price=price,
        currency=currency,
        stops="",
        multipass_url=multipass_url,
        wizzair_url=wizzair_url,
    )
