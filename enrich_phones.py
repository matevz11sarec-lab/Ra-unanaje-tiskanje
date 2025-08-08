#!/usr/bin/env python3
import argparse
import sys

from utils.io import read_input_csv, write_outputs
from core.enrich import run_enrichment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Phone Enricher (bizi.si + companywall.si)')
    parser.add_argument('--input', required=True, help='Input CSV path (UTF-8) with required column "name" and optional "bizi_url"')
    parser.add_argument('--out', required=True, help='Output CSV path for all rows; a second file with _only suffix will also be created')
    parser.add_argument('--headful', action='store_true', help='Run Chromium in headful (visible) mode')
    parser.add_argument('--auth-state', default='', help='Path to Playwright storage state (auth_state.json) to enable logged-in view if available')
    parser.add_argument('--min-delay', type=float, default=1.5, help='Minimum delay between navigations in seconds (default 1.5)')
    parser.add_argument('--max-delay', type=float, default=3.5, help='Maximum delay between navigations in seconds (default 3.5)')
    return parser.parse_args()


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

    def progress_cb(current: int, total: int, name: str, message: str) -> None:
        print(f"[{current}/{total}] {name} -> {message}")

    df_res, found_count, total = run_enrichment(
        df=df,
        headful=args.headful,
        auth_state=args.auth_state if args.auth_state else None,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        progress_cb=progress_cb,
    )

    # Write outputs
    all_path, only_path = write_outputs(df_res, args.out)

    # Stats
    success_pct = (found_count / total * 100.0) if total else 0.0
    print('\nDone.')
    print(f"All companies: {total}")
    print(f"Phones found: {found_count}")
    print(f"Success rate: {success_pct:.1f}%")
    print(f"Saved: {all_path}")
    print(f"Saved: {only_path}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())