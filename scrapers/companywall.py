import urllib.parse
from typing import Optional, Tuple
from playwright.sync_api import Page

from utils.phones import find_phone_on_page
from utils.browser import navigate_with_retries, random_delay

CW_BASE = 'https://www.companywall.si'
CW_SEARCH_URL = CW_BASE + '/iskanje?q={query}'


def _open_first_relevant_result(page: Page, company_name: str) -> bool:
    """Attempt to open the first relevant companywall.si result.

    Returns True if navigation to a result was attempted and succeeded, else False.
    """
    selectors = [
        'a[href*="/podjetje/"]',
        'a[href*="/firma/"]',
        'a[href^="/"]',
        'a[href^="https://www.companywall.si/"]',
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
                    url = href if href_lower.startswith('http') else urllib.parse.urljoin(CW_BASE, href)
                    if 'companywall.si' not in url:
                        continue
                    try:
                        text = link.inner_text(timeout=1000).strip().lower()
                    except Exception:
                        text = ''
                    if company_name.lower() in text or '/podjetje/' in url or '/firma/' in url:
                        try:
                            navigate_with_retries(page, url)
                            return True
                        except Exception:
                            continue
        except Exception:
            continue
    return False


def search_and_extract(page: Page, company_name: str, min_delay: float, max_delay: float) -> Tuple[Optional[str], str]:
    """Search companywall.si by company name and extract phone from the first relevant result."""
    try:
        query = urllib.parse.quote(company_name)
        search_url = CW_SEARCH_URL.format(query=query)
        navigate_with_retries(page, search_url)
        random_delay(min_delay, max_delay)

        opened = _open_first_relevant_result(page, company_name)
        if not opened:
            return None, 'companywall.si (no results)'

        random_delay(min_delay, max_delay)
        phone = find_phone_on_page(page)
        if phone:
            return phone, 'companywall.si'
        return None, 'companywall.si (no phone)'
    except Exception as exc:  # noqa: BLE001
        return None, f'companywall.si (error: {type(exc).__name__})'