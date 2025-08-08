import os
from typing import Tuple, Union, IO
import pandas as pd

REQUIRED_COLUMNS = ['name']
OPTIONAL_COLUMNS = ['bizi_url']


def _postprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    # Normalize column names (strip whitespace)
    df.columns = [str(c).strip() for c in df.columns]
    # Ensure optional columns exist for consistent processing
    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = ''
    return df


def read_input_csv(source: Union[str, IO[bytes], IO[str]]) -> pd.DataFrame:
    """Read input CSV with robust delimiter and encoding handling.

    - Tries UTF-8 and UTF-8 with BOM
    - Auto-detects delimiter (comma/semicolon) using engine='python'
    - Falls back to explicit semicolon, then comma
    """
    last_error = None
    for encoding in ('utf-8', 'utf-8-sig'):
        # 1) Autodetect delimiter
        try:
            df = pd.read_csv(
                source,
                dtype=str,
                keep_default_na=False,
                encoding=encoding,
                sep=None,
                engine='python',
            )
            df = _postprocess_df(df)
            for col in REQUIRED_COLUMNS:
                if col not in df.columns:
                    raise ValueError(f"Missing required column '{col}' in input CSV")
            return df
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        # 2) Explicit semicolon
        try:
            df = pd.read_csv(
                source,
                dtype=str,
                keep_default_na=False,
                encoding=encoding,
                sep=';',
                engine='python',
            )
            df = _postprocess_df(df)
            for col in REQUIRED_COLUMNS:
                if col not in df.columns:
                    raise ValueError(f"Missing required column '{col}' in input CSV")
            return df
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        # 3) Explicit comma
        try:
            df = pd.read_csv(
                source,
                dtype=str,
                keep_default_na=False,
                encoding=encoding,
                sep=',',
                engine='python',
            )
            df = _postprocess_df(df)
            for col in REQUIRED_COLUMNS:
                if col not in df.columns:
                    raise ValueError(f"Missing required column '{col}' in input CSV")
            return df
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise ValueError(f"Failed to read input CSV. Last error: {last_error}")


def write_outputs(df_all: pd.DataFrame, out_main_path: str) -> Tuple[str, str]:
    """Write the full dataset and the filtered dataset.

    Returns the tuple of written file paths: (all_rows_path, phones_only_path)
    """
    # Ensure columns are in a stable order: original + phone + source
    if 'phone' not in df_all.columns:
        df_all['phone'] = ''
    if 'source' not in df_all.columns:
        df_all['source'] = ''

    # Write the main output at the provided path
    df_all.to_csv(out_main_path, index=False, encoding='utf-8')

    # Derive the phones-only path by inserting _only before extension
    base, ext = os.path.splitext(out_main_path)
    phones_only_path = f"{base}_only{ext or '.csv'}"

    df_phones_only = df_all[df_all['phone'].astype(str).str.strip() != ''].copy()
    df_phones_only.to_csv(phones_only_path, index=False, encoding='utf-8')

    return out_main_path, phones_only_path