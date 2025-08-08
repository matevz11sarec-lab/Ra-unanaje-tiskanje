import os
from typing import Tuple
import pandas as pd

REQUIRED_COLUMNS = ['name']
OPTIONAL_COLUMNS = ['bizi_url']


def read_input_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding='utf-8')
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in input CSV")
    # Ensure optional columns exist for consistent processing
    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = ''
    return df


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