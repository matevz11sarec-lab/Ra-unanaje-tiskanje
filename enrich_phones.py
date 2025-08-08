#!/usr/bin/env python3
import argparse
import sys
from typing import Tuple

import pandas as pd

from utils.io import read_input_csv, write_outputs
from utils.browser import create_browser, random_delay
from scrapers.bizi import try_direct_profile as bizi_try_direct, search_and_extract as bizi_search
from scrapers.companywall import search_and_extract as cw_search


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Phone Enricher (bizi.si + companywall.si)')
    parser.add_argument('--input', required=True, help='Input CSV path (UTF-8) with required column "name" and optional "bizi_url"')
    parser.add_argument('--out', required=True, help='Output CSV path for all rows; a second file with _only suffix will also be created')
    parser.add_argument('--headful', action='store_true', help='Run Chromium in headful (visible) mode')
    parser.add_argument('--auth-state', default='', help='Path to Playwright storage state (auth_state.json) to enable logged-in view if available')
    parser.add_argument('--min-delay', type=float, default=1.5, help='Minimum delay between navigations in seconds (default 1.5)')
    parser.add_argument('--max-delay', type=float, default=3.5, help='Maximum delay between navigations in seconds (default 3.5)')
    return parser.parse_args()


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


def main() -> int:
    args = parse_args()

    # Ensure min_delay <= max_delay
    if args.min_delay > args.max_delay:
        print('Error: --min-delay must be <= --max-delay', file=sys.stderr)
        return 2

    try:
        df = read_input_csv(args.input)
    except Exception as exc:  # noqa: BLE001
        print(f'Failed to read input CSV: {exc}', file=sys.stderr)
        return 2

    # Prepare new columns
    df['phone'] = ''
    df['source'] = ''

    browser = context = page = playwright = None
    try:
        browser, context, page, playwright = create_browser(
            headful=args.headful,
            auth_state_path=args.auth_state if args.auth_state else None,
            default_timeout_ms=20000,
        )

        total = len(df)
        found_count = 0

        for idx, row in df.iterrows():
            name = (row.get('name') or '').strip()
            bizi_url = (row.get('bizi_url') or '').strip()

            progress_prefix = f"[{idx + 1}/{total}] {name}"
            try:
                phone, source = process_company(page, name, bizi_url, args.min_delay, args.max_delay)
                df.at[idx, 'phone'] = phone
                df.at[idx, 'source'] = source
                if phone:
                    found_count += 1
                    print(f"{progress_prefix} -> FOUND via {source}: {phone}")
                else:
                    print(f"{progress_prefix} -> {source}")
            except Exception as exc:  # noqa: BLE001
                error_msg = f"error: {type(exc).__name__}"
                df.at[idx, 'phone'] = ''
                df.at[idx, 'source'] = error_msg
                print(f"{progress_prefix} -> {error_msg}")
                # Continue to next company
                continue

            # Polite delay between companies
            random_delay(args.min_delay, args.max_delay)

        # Write outputs
        all_path, only_path = write_outputs(df, args.out)

        # Stats
        success_pct = (found_count / total * 100.0) if total else 0.0
        print('\nDone.')
        print(f"All companies: {total}")
        print(f"Phones found: {found_count}")
        print(f"Success rate: {success_pct:.1f}%")
        print(f"Saved: {all_path}")
        print(f"Saved: {only_path}")

        return 0
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


if __name__ == '__main__':
    raise SystemExit(main())