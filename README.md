## Phone Enricher (bizi.si + companywall.si)

Python 3.10+ tool that enriches a CSV of companies with phone numbers scraped from public pages on `bizi.si` and `companywall.si` using Playwright (Chromium) and pandas.

- Input CSV (UTF-8) must contain column `name` and may contain column `bizi_url`.
- Output consists of two CSV files:
  - The full dataset at the path given by `--out`, enriched with `phone` and `source` columns
  - A filtered dataset saved alongside with `_only` suffix, containing only rows where a phone was found

### Features
- Uses Playwright (Chromium) with a standard desktop Chrome User-Agent
- Optional `auth_state.json` (Playwright storage state) for logged-in views if available
- Robust extraction: prefers `<a href="tel:">`, otherwise falls back to regex on page text
- Regex covers Slovenian phone formats: `+386` and `0xx` with spaces or dashes (e.g. `+386 41 123 456`, `01 234 56 78`, `040-123-456`)
- Random delay between navigations (default 1.5–3.5s) and 20s navigation timeout
- Retry mechanism (2 attempts) for page navigation
- Prints progress `[current/total] company name -> status`, does not abort on errors
- No parallel execution; includes polite throttling

### Install
1) Create and activate a virtual environment (recommended).

2) Install dependencies:

```bash
pip install -r requirements.txt
```

3) Install Playwright browsers (one-time):

```bash
python -m playwright install chromium
```

### Usage

```bash
python enrich_phones.py \
  --input input.csv \
  --out output_with_phones.csv \
  --min-delay 1.5 \
  --max-delay 3.5
```

Optional flags:
- `--headful` to see the browser window
- `--auth-state auth_state.json` to load Playwright storage state if available

Example input `input.csv`:

```csv
name,bizi_url
Podjetje d.o.o.,https://www.bizi.si/podjetje/podjetje-d-o-o/1234567/
Drugo Podjetje d.o.o.,
```

Example outputs:
- `output_with_phones.csv` (as specified by `--out`)
- `output_with_phones_only.csv` will be saved as `output_with_phones_only.csv` if `--out` is `output_with_phones.csv`, otherwise as `<out>_only.csv`

### How it works
- If `bizi_url` is provided, the tool opens it and tries to extract a phone via `<a href="tel:">` first; if not present, it scans the page body using the regex.
- If not found, it performs a search on `bizi.si`, opens the first relevant result, and repeats extraction.
- If still not found, it searches `companywall.si`, opens the first relevant result, and repeats extraction.
- If no phone is found, the row is kept with an empty `phone` and `source` describing the last site tried (e.g., `companywall.si (no phone)`).

### Notes
- This tool accesses publicly available data for personal/internal use. Respect each website's terms of use.
- CSS selectors for search results are kept simple and include fallbacks; adjust them in `scrapers/bizi.py` and `scrapers/companywall.py` if site markup changes.
- The regex is defined in `utils/phones.py` as:

```python
PHONE_REGEX = re.compile(r'(?:\+386\s?\d{1,2}[\s\-]?\d{3}[\s\-]?\d{3,4}|0\d{1,2}[\s\-]?\d{3}[\s\-]?\d{3,4})')
```

- Normalization collapses multiple spaces but preserves separators.