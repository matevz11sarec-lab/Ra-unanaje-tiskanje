from typing import Callable, Optional, Tuple
import urllib.parse
import pandas as pd

from utils.browser import create_browser, random_delay, navigate_with_retries
from utils.websites import find_website_on_page
from scrapers.bizi import BIZI_BASE, BIZI_SEARCH_URL
from scrapers.companywall import CW_BASE, CW_SEARCH_URL

ProgressCallback = Optional[Callable[[int, int, str, str], None]]


def _open_bizi_profile(page, company_name: str) -> bool:
    # Reuse selector strategy similar to scrapers.bizi
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
                    if not href or href.lower().startswith(('mailto:', 'tel:', 'javascript:')):
                        continue
                    url = href if href.lower().startswith('http') else urllib.parse.urljoin(BIZI_BASE, href)
                    if 'bizi.si' not in url:
                        continue
                    try:
                        text = link.inner_text(timeout=1000).strip().lower()
                    except Exception:
                        text = ''
                    if company_name.lower() in text or '/podjetje/' in url:
                        navigate_with_retries(page, url)
                        return True
        except Exception:
            continue
    return False


def _open_companywall_profile(page, company_name: str) -> bool:
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
                    if not href or href.lower().startswith(('mailto:', 'tel:', 'javascript:')):
                        continue
                    url = href if href.lower().startswith('http') else urllib.parse.urljoin(CW_BASE, href)
                    if 'companywall.si' not in url:
                        continue
                    try:
                        text = link.inner_text(timeout=1000).strip().lower()
                    except Exception:
                        text = ''
                    if company_name.lower() in text or '/podjetje/' in url or '/firma/' in url:
                        navigate_with_retries(page, url)
                        return True
        except Exception:
            continue
    return False


def run_agency_enrichment(
    df: pd.DataFrame,
    headful: bool,
    auth_state: Optional[str],
    min_delay: float,
    max_delay: float,
    progress_cb: ProgressCallback = None,
    always_search_phone: bool = False,
) -> Tuple[pd.DataFrame, int, int]:
    """For each company, check website first, optionally still search phone.

    If website exists: set website_status='ima spletno stran'.
    If not or always_search_phone=True: search phone via bizi/companywall.
    """
    if 'name' not in df.columns:
        raise ValueError("Input DataFrame is missing required column 'name'")
    if 'bizi_url' not in df.columns:
        df['bizi_url'] = ''

    df = df.copy()
    df['website'] = ''
    df['website_status'] = ''
    df['phone'] = ''
    df['source'] = ''

    browser = context = page = playwright = None
    try:
        browser, context, page, playwright = create_browser(
            headful=headful,
            auth_state_path=auth_state if auth_state else None,
            default_timeout_ms=20000,
        )
        total = len(df)
        found_phones = 0

        for idx, row in df.iterrows():
            name = (row.get('name') or '').strip()
            bizi_url = (row.get('bizi_url') or '').strip()

            try:
                has_website = False

                # 1) If bizi_url provided, open and look for website
                if bizi_url:
                    try:
                        navigate_with_retries(page, bizi_url)
                        random_delay(min_delay, max_delay)
                        site = find_website_on_page(page)
                        if site:
                            df.at[idx, 'website'] = site
                            df.at[idx, 'website_status'] = 'ima spletno stran'
                            has_website = True
                            if progress_cb:
                                progress_cb(idx + 1, total, name, 'ima spletno stran')
                    except Exception:
                        pass

                # 2) If no website yet, try bizi search
                if not has_website:
                    try:
                        search_url = BIZI_SEARCH_URL.format(query=urllib.parse.quote(name))
                        navigate_with_retries(page, search_url)
                        random_delay(min_delay, max_delay)
                        if _open_bizi_profile(page, name):
                            random_delay(min_delay, max_delay)
                            site = find_website_on_page(page)
                            if site:
                                df.at[idx, 'website'] = site
                                df.at[idx, 'website_status'] = 'ima spletno stran'
                                has_website = True
                                if progress_cb:
                                    progress_cb(idx + 1, total, name, 'ima spletno stran')
                    except Exception:
                        pass

                # 3) If still no website, try companywall search
                if not has_website:
                    try:
                        search_url = CW_SEARCH_URL.format(query=urllib.parse.quote(name))
                        navigate_with_retries(page, search_url)
                        random_delay(min_delay, max_delay)
                        if _open_companywall_profile(page, name):
                            random_delay(min_delay, max_delay)
                            site = find_website_on_page(page)
                            if site:
                                df.at[idx, 'website'] = site
                                df.at[idx, 'website_status'] = 'ima spletno stran'
                                has_website = True
                                if progress_cb:
                                    progress_cb(idx + 1, total, name, 'ima spletno stran')
                    except Exception:
                        pass

                # 4) Phone search when needed
                from utils.phones import find_phone_on_page

                if not has_website:
                    df.at[idx, 'website_status'] = 'nima spletne strani'

                if always_search_phone or not has_website:
                    phone = find_phone_on_page(page) or ''
                    if phone:
                        df.at[idx, 'phone'] = phone
                        # If we are on bizi/companywall, choose accordingly
                        df.at[idx, 'source'] = 'bizi.si' if 'bizi.si' in (page.url or '') else 'companywall.si'
                        found_phones += 1
                        if progress_cb:
                            progress_cb(idx + 1, total, name, f"FOUND: {phone}")
                        random_delay(min_delay, max_delay)
                        continue

                    # Bizi for phone
                    try:
                        search_url = BIZI_SEARCH_URL.format(query=urllib.parse.quote(name))
                        navigate_with_retries(page, search_url)
                        random_delay(min_delay, max_delay)
                        if _open_bizi_profile(page, name):
                            random_delay(min_delay, max_delay)
                            phone = find_phone_on_page(page) or ''
                            if phone:
                                df.at[idx, 'phone'] = phone
                                df.at[idx, 'source'] = 'bizi.si'
                                found_phones += 1
                                if progress_cb:
                                    progress_cb(idx + 1, total, name, f"FOUND: {phone}")
                                random_delay(min_delay, max_delay)
                                continue
                    except Exception:
                        pass

                    # Companywall for phone
                    try:
                        search_url = CW_SEARCH_URL.format(query=urllib.parse.quote(name))
                        navigate_with_retries(page, search_url)
                        random_delay(min_delay, max_delay)
                        if _open_companywall_profile(page, name):
                            random_delay(min_delay, max_delay)
                            phone = find_phone_on_page(page) or ''
                            if phone:
                                df.at[idx, 'phone'] = phone
                                df.at[idx, 'source'] = 'companywall.si'
                                found_phones += 1
                                if progress_cb:
                                    progress_cb(idx + 1, total, name, f"FOUND: {phone}")
                                random_delay(min_delay, max_delay)
                                continue
                    except Exception:
                        pass

                    # No phone
                    if not has_website:
                        df.at[idx, 'source'] = 'ni telefonske številke'
                        if progress_cb:
                            progress_cb(idx + 1, total, name, 'ni telefonske številke')

                random_delay(min_delay, max_delay)

            except Exception as exc:  # noqa: BLE001
                df.at[idx, 'website_status'] = 'napaka'
                df.at[idx, 'source'] = f'error: {type(exc).__name__}'
                if progress_cb:
                    progress_cb(idx + 1, total, name, f'error: {type(exc).__name__}')
                continue

        return df, found_phones, total
    finally:
        try:
            if context:
                context.close()
            if browser:
                browser.close()
            if playwright:
                playwright.stop()
        except Exception:
            pass