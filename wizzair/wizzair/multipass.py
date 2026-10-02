from __future__ import annotations

import asyncio
import string

from playwright.async_api import BrowserContext, Error as PlaywrightError, Page

from wizzair.config import WALLETS_URL, Settings
from wizzair.models import Destination

ORIGIN_QUERIES = {
    "KRK": ("Krak", "Kraków"),
    "KTW": ("Katow", "Katowice"),
    "WAW": ("Warsz", "Warszawa"),
    "GDN": ("Gda", "Gdańsk"),
    "WRO": ("Wroc", "Wrocław"),
    "POZ": ("Pozn", "Poznań"),
}

LOGIN_ERROR_SELECTORS = (
    "#input-error",
    ".kc-feedback-text",
    ".alert-error",
    ".pf-c-alert__title",
    '[class*="error"]',
)


async def login(context: BrowserContext, settings: Settings) -> Page:
    page = await context.new_page()
    timeout_ms = int(settings.http_timeout * 1000)
    await page.goto(WALLETS_URL, wait_until="domcontentloaded", timeout=timeout_ms)

    if _needs_login(page.url):
        await _submit_login(page, settings, timeout_ms=timeout_ms)

    if not _is_logged_in(page.url):
        await _raise_login_failure(page, settings)

    await page.wait_for_timeout(1500)
    await dismiss_modals(page)
    return page


async def _submit_login(page: Page, settings: Settings, *, timeout_ms: int) -> None:
    await page.wait_for_selector("#username", timeout=timeout_ms)
    await page.fill("#username", settings.email)
    await page.fill("#password", settings.password)

    try:
        async with page.expect_navigation(timeout=timeout_ms, wait_until="domcontentloaded"):
            await page.click("#kc-login")
    except PlaywrightError:
        pass

    deadline = asyncio.get_event_loop().time() + (timeout_ms / 1000)
    while asyncio.get_event_loop().time() < deadline:
        if _is_logged_in(page.url):
            return

        login_error = await _read_login_error(page)
        if login_error:
            raise RuntimeError(f"Logowanie nie powiodło się: {login_error}")

        if _needs_login(page.url) and "login-actions/authenticate" not in page.url:
            login_error = await _read_login_error(page)
            if login_error:
                raise RuntimeError(f"Logowanie nie powiodło się: {login_error}")

        try:
            await page.wait_for_load_state("domcontentloaded", timeout=2000)
        except PlaywrightError:
            pass
        await page.wait_for_timeout(1000)

    await _raise_login_failure(page, settings)


async def _read_login_error(page: Page) -> str:
    for selector in LOGIN_ERROR_SELECTORS:
        locator = page.locator(selector).first
        if await locator.count() == 0:
            continue
        try:
            text = (await locator.inner_text(timeout=1000)).strip()
        except PlaywrightError:
            continue
        if text and "error" not in text.lower()[:6]:
            return text
        if text:
            return text
    return ""


def _needs_login(url: str) -> bool:
    lowered = url.lower()
    return "openid-connect/auth" in lowered or "login-actions" in lowered


def _is_logged_in(url: str) -> bool:
    lowered = url.lower()
    return "multipass.wizzair.com" in lowered and (
        "wallets" in lowered
        or "private-page" in lowered
        or "/availability/" in lowered
    )


async def _raise_login_failure(page: Page, settings: Settings) -> None:
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    screenshot = logs_dir / "login_failed.png"
    try:
        await page.screenshot(path=str(screenshot), full_page=True)
    except PlaywrightError:
        screenshot = None

    login_error = await _read_login_error(page)
    hints = [
        "Sprawdź WIZZAIR_EMAIL i WIZZAIR_PASSWORD w pliku .env",
        "Spróbuj logowania z widoczną przeglądarką: python -m wizzair login --headed",
        "Na Macu headless Chrome bywa blokowany — użyj --headed lub zapisaną sesję",
    ]
    if screenshot:
        hints.append(f"Zrzut ekranu: {screenshot}")

    detail = login_error or f"utknął na URL: {page.url}"
    raise RuntimeError(f"Nie udało się zalogować do Wizz Multipass ({detail}).\n" + "\n".join(f"- {h}" for h in hints))


async def dismiss_modals(page: Page) -> None:
    for selector in (".CvoModal button", ".CvoModal .cvo-button"):
        button = page.locator(selector).first
        if await button.count() > 0:
            try:
                await button.click(timeout=1500)
            except PlaywrightError:
                pass
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)


async def extract_pass_id(page: Page, settings: Settings) -> str:
    if settings.pass_id:
        return settings.pass_id

    pass_id = await page.evaluate(
        """() => {
            if (window.DD_RUM && typeof window.DD_RUM.getUser === 'function') {
                const user = window.DD_RUM.getUser();
                if (user && user.pass_id) return user.pass_id;
            }
            return null;
        }"""
    )
    if pass_id:
        return pass_id

    html = await page.content()
    from wizzair.api import extract_pass_id as parse_pass_id

    parsed = parse_pass_id(html)
    if parsed:
        return parsed
    raise RuntimeError("Could not determine Wizz Multipass pass_id from the wallets page.")


async def discover_destinations(page: Page, origin: str) -> list[Destination]:
    query, pick = ORIGIN_QUERIES.get(origin.upper(), (origin[:3], origin))
    await page.goto(WALLETS_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(1200)
    await dismiss_modals(page)

    origin_input = page.locator('input[id^="autocomplete-origin"]').first
    await origin_input.click()
    await origin_input.fill("")
    await origin_input.type(query, delay=30)
    await page.wait_for_timeout(1000)
    await page.locator("ul.autocomplete-result-list:visible li").filter(has_text=pick).first.click()
    await page.wait_for_timeout(500)

    destinations: set[str] = set()
    for letter in string.ascii_lowercase:
        dest_input = page.locator('input[id^="autocomplete-destination"]').first
        await dest_input.click()
        await dest_input.fill("")
        await dest_input.type(letter, delay=20)
        await page.wait_for_timeout(500)
        for label in await page.locator("ul.autocomplete-result-list:visible li").all_inner_texts():
            label = label.strip()
            if label:
                destinations.add(label)

    parsed: list[Destination] = []
    for label in sorted(destinations):
        code = _extract_iata(label)
        if code:
            parsed.append(Destination(code=code, label=label))
    return parsed


def _extract_iata(label: str) -> str | None:
    if "(" not in label or ")" not in label:
        return None
    return label.rsplit("(", 1)[-1].rstrip(")").strip().upper()
