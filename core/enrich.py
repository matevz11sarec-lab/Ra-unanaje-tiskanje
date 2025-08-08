from typing import Callable, Optional, Tuple
import pandas as pd

from utils.browser import create_browser, random_delay
from scrapers.bizi import try_direct_profile as bizi_try_direct, search_and_extract as bizi_search
from scrapers.companywall import search_and_extract as cw_search

ProgressCallback = Optional[Callable[[int, int, str, str], None]]


def process_company(page, name: str, bizi_url: str, min_delay: float, max_delay: float) -> Tuple[str, str]:
    """Process a single company: try bizi direct (if URL), then bizi search, then companywall search.

    Returns (phone, source).
    """
    last_source = ''

    # 1) Direct bizi profile if provided
    if bizi_url.strip():
        phone, source = bizi_try_direct(page, bizi_url.strip(), min_delay, max_delay)
        if phone:
            return phone, source
        last_source = source
        random_delay(min_delay, max_delay)

    # 2) Bizi search
    phone, source = bizi_search(page, name, min_delay, max_delay)
    if phone:
        return phone, source
    last_source = source
    random_delay(min_delay, max_delay)

    # 3) Companywall search
    phone, source = cw_search(page, name, min_delay, max_delay)
    if phone:
        return phone, source
    last_source = source

    # Not found anywhere
    return '', last_source or 'no phone'


def run_enrichment(
    df: pd.DataFrame,
    headful: bool,
    auth_state: Optional[str],
    min_delay: float,
    max_delay: float,
    progress_cb: ProgressCallback = None,
) -> Tuple[pd.DataFrame, int, int]:
    """Run enrichment on a DataFrame and return (df_with_results, found_count, total)."""
    # Ensure required columns exist
    if 'name' not in df.columns:
        raise ValueError("Input DataFrame is missing required column 'name'")
    if 'bizi_url' not in df.columns:
        df['bizi_url'] = ''

    # Prepare new columns
    df = df.copy()
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
        found_count = 0

        for idx, row in df.iterrows():
            name = (row.get('name') or '').strip()
            bizi_url = (row.get('bizi_url') or '').strip()
            try:
                phone, source = process_company(page, name, bizi_url, min_delay, max_delay)
                df.at[idx, 'phone'] = phone
                df.at[idx, 'source'] = source
                if phone:
                    found_count += 1
                    if progress_cb:
                        progress_cb(idx + 1, total, name, f"FOUND via {source}: {phone}")
                else:
                    if progress_cb:
                        progress_cb(idx + 1, total, name, source)
            except Exception as exc:  # noqa: BLE001
                error_msg = f"error: {type(exc).__name__}"
                df.at[idx, 'phone'] = ''
                df.at[idx, 'source'] = error_msg
                if progress_cb:
                    progress_cb(idx + 1, total, name, error_msg)
                continue

            # Polite delay between companies
            random_delay(min_delay, max_delay)

        return df, found_count, total
    finally:
        # Close browser resources
        try:
            if context:
                context.close()
            if browser:
                browser.close()
            if playwright:
                playwright.stop()
        except Exception:
            pass