import os
import random
import time
from typing import Optional, Tuple
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

# A standard Chrome desktop user agent
CHROME_DESKTOP_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
)


def create_browser(headful: bool = False, auth_state_path: Optional[str] = None,
                   default_timeout_ms: int = 20000) -> Tuple[Browser, BrowserContext, Page, object]:
    """Create a Chromium browser, context, and page with optional storage state.

    Returns a tuple (browser, context, page, playwright_handle).
    Caller is responsible for closing in reverse order and stopping playwright.
    """
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=not headful)

    storage_state = None
    if auth_state_path and os.path.exists(auth_state_path):
        storage_state = auth_state_path

    context = browser.new_context(
        user_agent=CHROME_DESKTOP_UA,
        storage_state=storage_state,
    )

    # Apply default timeouts
    context.set_default_timeout(default_timeout_ms)
    context.set_default_navigation_timeout(default_timeout_ms)

    page = context.new_page()
    return browser, context, page, playwright


def random_delay(min_delay_s: float, max_delay_s: float) -> None:
    """Sleep for a random delay between min and max seconds (inclusive)."""
    delay = random.uniform(min_delay_s, max_delay_s)
    time.sleep(delay)


def navigate_with_retries(page: Page, url: str, timeout_ms: int = 20000, attempts: int = 2) -> None:
    """Navigate to a URL with a simple retry mechanism."""
    last_exc: Optional[Exception] = None
    for attempt in range(1, attempts + 1):
        try:
            page.goto(url, timeout=timeout_ms, wait_until='load')
            return
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < attempts:
                # Short jitter before retrying
                time.sleep(0.7)
                continue
            raise last_exc