from __future__ import annotations

import asyncio
from typing import Literal

import httpx

from travel_agent.clean import looks_like_antibot
from travel_agent.config import Settings
from travel_agent.models import FetchResult
from travel_agent.sites import Site

FetchMode = Literal["auto", "http", "browser"]


async def fetch_site(
    settings: Settings,
    site: Site,
    *,
    mode: FetchMode,
    browser_pool: BrowserPool | None,
) -> FetchResult:
    if mode == "browser":
        return await _fetch_with_browser(settings, site, browser_pool)

    http_result = await _fetch_with_http(settings, site)
    if mode == "http":
        return http_result

    if _needs_browser_retry(http_result, settings):
        browser_result = await _fetch_with_browser(settings, site, browser_pool)
        if browser_result.text:
            return browser_result
    return http_result


def _needs_browser_retry(result: FetchResult, settings: Settings) -> bool:
    if result.error:
        return True
    if len(result.text) < settings.browser_retry_min_chars:
        return True
    return looks_like_antibot(result.text)


async def _fetch_with_http(settings: Settings, site: Site) -> FetchResult:
    headers = {
        "User-Agent": settings.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
    }
    timeout = httpx.Timeout(settings.http_timeout)
    last_error = ""
    async with httpx.AsyncClient(
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
        http2=True,
    ) as client:
        for url in site.urls:
            try:
                response = await client.get(url)
                if response.status_code >= 400:
                    last_error = f"HTTP {response.status_code} for {url}"
                    continue
                text = response.text
                if text.strip():
                    return FetchResult(site.id, text, "http", str(response.url))
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
    return FetchResult(site.id, "", "http", site.urls[0], error=last_error)


async def _fetch_with_browser(
    settings: Settings,
    site: Site,
    browser_pool: BrowserPool | None,
) -> FetchResult:
    if browser_pool is None:
        return FetchResult(
            site.id,
            "",
            "browser",
            site.urls[0],
            error="Playwright not available. Run: playwright install chromium",
        )
    last_error = ""
    for url in site.urls:
        try:
            text, final_url = await browser_pool.fetch(url)
            if text.strip():
                return FetchResult(site.id, text, "browser", final_url)
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
    return FetchResult(site.id, "", "browser", site.urls[0], error=last_error)


class BrowserPool:
    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self._context = None
        self._lock = asyncio.Lock()

    async def start(self, user_agent: str) -> None:
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        self._context = await self._browser.new_context(user_agent=user_agent, locale="pl-PL")

    async def close(self) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def fetch(self, url: str) -> tuple[str, str]:
        if not self._context:
            raise RuntimeError("Browser pool not started")
        async with self._lock:
            page = await self._context.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await _dismiss_cookie_banners(page)
                try:
                    await page.wait_for_function(
                        "() => (document.body && document.body.innerText.length > 600)",
                        timeout=10000,
                    )
                except Exception:
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass
                text = await page.content()
                return text, page.url
            finally:
                await page.close()


async def _dismiss_cookie_banners(page) -> None:
    selectors = [
        "button:has-text('Akceptuj')",
        "button:has-text('Zgadzam')",
        "button:has-text('Accept')",
        "#onetrust-accept-btn-handler",
        ".didomi-continue-without-agreeing",
    ]
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.is_visible(timeout=1000):
                await locator.click(timeout=1000)
                return
        except Exception:
            continue
