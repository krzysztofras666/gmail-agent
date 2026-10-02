from __future__ import annotations

from pathlib import Path

from playwright.async_api import Browser, BrowserContext, Playwright

from wizzair.config import Settings, default_session_path


async def open_browser_context(
    playwright: Playwright,
    settings: Settings,
    *,
    session_path: Path | None = None,
) -> tuple[Browser, BrowserContext]:
    launch_kwargs: dict = {"headless": settings.headless}
    browser: Browser | None = None
    if settings.use_chrome:
        try:
            browser = await playwright.chromium.launch(channel="chrome", **launch_kwargs)
        except Exception:
            browser = None
    if browser is None:
        browser = await playwright.chromium.launch(**launch_kwargs)

    context_kwargs: dict = {
        "locale": f"{settings.locale}-PL",
        "user_agent": settings.user_agent,
    }
    path = session_path or settings.storage_state_path
    if path.exists():
        context_kwargs["storage_state"] = str(path)

    context = await browser.new_context(**context_kwargs)
    return browser, context


async def persist_session(context: BrowserContext, settings: Settings) -> Path:
    path = settings.storage_state_path
    path.parent.mkdir(parents=True, exist_ok=True)
    await context.storage_state(path=str(path))
    return path
