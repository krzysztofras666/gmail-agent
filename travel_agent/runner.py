from __future__ import annotations

import asyncio
from typing import Literal

from travel_agent.aggregate import aggregate_offers
from travel_agent.clean import clean_html
from travel_agent.config import Settings
from travel_agent.extract import extract_offers
from travel_agent.fetch import BrowserPool, FetchMode, fetch_site
from travel_agent.models import RunResult, SiteDiagnostic
from travel_agent.sites import Site, get_sites

FetchModeArg = Literal["auto", "http", "browser"]


async def run_agent(
    settings: Settings,
    *,
    site_ids: list[str] | None = None,
    max_per_destination: int | None = None,
    fetch_mode: FetchModeArg = "auto",
) -> RunResult:
    sites = get_sites(site_ids)
    limit = max_per_destination or settings.max_offers_per_dest
    semaphore = asyncio.Semaphore(settings.fetch_concurrency)

    browser_pool: BrowserPool | None = None
    if fetch_mode in ("auto", "browser"):
        try:
            browser_pool = BrowserPool()
            await browser_pool.start(settings.user_agent)
        except Exception:
            browser_pool = None

    async def process_site(site: Site) -> tuple[list, SiteDiagnostic]:
        async with semaphore:
            fetch_result = await fetch_site(
                settings,
                site,
                mode=fetch_mode,
                browser_pool=browser_pool,
            )
            if fetch_result.error and not fetch_result.text:
                return [], SiteDiagnostic(
                    site_id=site.id,
                    site_name=site.name,
                    engine=fetch_result.engine,
                    chars_fetched=0,
                    offers_extracted=0,
                    error=fetch_result.error,
                )

            cleaned = clean_html(
                fetch_result.text,
                is_rss=site.is_rss,
                max_chars=settings.max_text_chars,
            )
            try:
                offers = extract_offers(settings, site, cleaned)
            except Exception as exc:  # noqa: BLE001
                return [], SiteDiagnostic(
                    site_id=site.id,
                    site_name=site.name,
                    engine=fetch_result.engine,
                    chars_fetched=len(cleaned),
                    offers_extracted=0,
                    error=str(exc),
                )

            return offers, SiteDiagnostic(
                site_id=site.id,
                site_name=site.name,
                engine=fetch_result.engine,
                chars_fetched=len(cleaned),
                offers_extracted=len(offers),
                error=fetch_result.error,
            )

    try:
        pairs = await asyncio.gather(*(process_site(site) for site in sites))
    finally:
        if browser_pool:
            await browser_pool.close()

    all_offers = []
    diagnostics = []
    for offers, diag in pairs:
        all_offers.extend(offers)
        diagnostics.append(diag)

    aggregated = aggregate_offers(all_offers, max_per_destination=limit)
    return RunResult(offers=aggregated, diagnostics=diagnostics)
