import urllib.parse
from typing import Optional, Tuple
from playwright.sync_api import Page

from utils.phones import find_phone_on_page
from utils.browser import navigate_with_retries, random_delay

BIZI_BASE = 'https://www.bizi.si'
BIZI_SEARCH_URL = BIZI_BASE + '/iskanje/?q={query}'


def _open_first_relevant_result(page: Page, company_name: str) -> bool:
    """Attempt to open the first relevant bizi.si profile result.

    Returns True if navigation to a result was attempted and succeeded, else False.
    """
    # Prefer typical profile URL patterns
    selectors = [
        'a[href*="/podjetje/"]',
        'a[href^="https://www.bizi.si/"]',
        'a[href^="/"]',
    ]

    for selector in selectors:
        try:
            loc = page.locator(selector)
            if loc.count() > 0:
                for i in range(min(loc.count(), 20)):
                    link = loc.nth(i)
                    href = link.get_attribute('href') or ''
                    if not href:
                        continue
                    href_lower = href.lower()
                    if href_lower.startswith('mailto:') or href_lower.startswith('tel:') or href_lower.startswith('javascript:'):
                        continue
                    # Expand relative URLs
                    url = href if href_lower.startswith('http') else urllib.parse.urljoin(BIZI_BASE, href)
                    # Heuristic: ensure domain and avoid obvious non-company pages
                    if 'bizi.si' not in url:
                        continue
                    # Prefer links whose text contains the company name
                    try:
                        text = link.inner_text(timeout=1000).strip().lower()
                    except Exception:
                        text = ''
                    if company_name.lower() in text or '/podjetje/' in url:
                        try:
                            navigate_with_retries(page, url)
                            return True
                        except Exception:
                            continue
        except Exception:
            continue
    return False


def try_direct_profile(page: Page, url: str, min_delay: float, max_delay: float) -> Tuple[Optional[str], str]:
    """Try to open a direct bizi.si profile URL and extract a phone."""
    try:
        navigate_with_retries(page, url)
        random_delay(min_delay, max_delay)
        phone = find_phone_on_page(page)
        if phone:
            return phone, 'bizi.si'
        return None, 'bizi.si (no phone)'
    except Exception as exc:  # noqa: BLE001
        return None, f'bizi.si (error: {type(exc).__name__})'


def search_and_extract(page: Page, company_name: str, min_delay: float, max_delay: float) -> Tuple[Optional[str], str]:
    """Search bizi.si by company name and extract phone from the first relevant result."""
    try:
        query = urllib.parse.quote(company_name)
        search_url = BIZI_SEARCH_URL.format(query=query)
        navigate_with_retries(page, search_url)
        random_delay(min_delay, max_delay)

        opened = _open_first_relevant_result(page, company_name)
        if not opened:
            return None, 'bizi.si (no results)'

        random_delay(min_delay, max_delay)
        phone = find_phone_on_page(page)
        if phone:
            return phone, 'bizi.si'
        return None, 'bizi.si (no phone)'
    except Exception as exc:  # noqa: BLE001
        return None, f'bizi.si (error: {type(exc).__name__})'