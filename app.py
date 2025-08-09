import io
import tempfile
from typing import Optional

import pandas as pd
import streamlit as st

from core.enrich import run_enrichment
from utils.io import read_input_csv

st.set_page_config(page_title='Phone Enricher (bizi.si + companywall.si)', layout='centered')
st.title('Phone Enricher (bizi.si + companywall.si)')

st.markdown('Naložite CSV datoteko z obveznim stolpcem `name` in opcijskim `bizi_url`.')

uploaded_csv = st.file_uploader('Vhodni CSV (UTF-8)', type=['csv'])
auth_state_file = st.file_uploader('auth_state.json (neobvezno)', type=['json'])

col1, col2 = st.columns(2)
with col1:
    min_delay = st.number_input('Min. zamik (sekunde)', min_value=0.5, max_value=10.0, value=1.5, step=0.1)
with col2:
    max_delay = st.number_input('Maks. zamik (sekunde)', min_value=0.5, max_value=15.0, value=3.5, step=0.1)

headful = st.checkbox('Prikaži brskalnik (headful)', value=False)

run_btn = st.button('Zaženi obogatitev', type='primary', use_container_width=True)

progress_placeholder = st.empty()
log_placeholder = st.empty()

if run_btn:
    if uploaded_csv is None:
        st.error('Najprej naložite CSV datoteko.')
    elif min_delay > max_delay:
        st.error('Min. zamik ne sme biti večji od maks. zamika.')
    else:
        try:
            # Use robust CSV reader with delimiter/encoding detection
            df_input = read_input_csv(uploaded_csv)
        except Exception as exc:  # noqa: BLE001
            st.error(f'Napaka pri branju CSV: {exc}')
        else:
            # Write auth_state to temp file if provided
            auth_state_path: Optional[str] = None
            if auth_state_file is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tf:
                    tf.write(auth_state_file.read())
                    auth_state_path = tf.name

            # Progress UI
            progress_bar = st.progress(0)
            logs = []

            def progress_cb(current: int, total: int, name: str, message: str) -> None:
                pct = int(current / max(total, 1) * 100)
                progress_bar.progress(pct)
                logs.append(f'[{current}/{total}] {name} -> {message}')
                # Show last 10 logs
                log_placeholder.write('\n'.join(logs[-10:]))

            with st.spinner('Izvajam...'):
                try:
                    df_res, found_count, total = run_enrichment(
                        df=df_input,
                        headful=headful,
                        auth_state=auth_state_path,
                        min_delay=float(min_delay),
                        max_delay=float(max_delay),
                        progress_cb=progress_cb,
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f'Napaka: {exc}')
                else:
                    success_pct = (found_count / total * 100.0) if total else 0.0
                    st.success(f'Končano. Najdenih številk: {found_count}/{total} ({success_pct:.1f}%).')

                    # Prepare downloads
                    csv_all = df_res.to_csv(index=False).encode('utf-8')
                    df_only = df_res[df_res['phone'].astype(str).str.strip() != ''].copy()
                    csv_only = df_only.to_csv(index=False).encode('utf-8')
                    # Minimal file: name, phone, source
                    try:
                        df_min = df_only[['name', 'phone', 'source']].copy()
                        csv_min = df_min.to_csv(index=False).encode('utf-8')
                    except Exception:
                        df_min = pd.DataFrame(columns=['name', 'phone', 'source'])
                        csv_min = df_min.to_csv(index=False).encode('utf-8')

                    st.download_button(
                        'Prenesi: output_with_phones.csv',
                        data=csv_all,
                        file_name='output_with_phones.csv',
                        mime='text/csv',
                        use_container_width=True,
                    )
                    st.download_button(
                        'Prenesi: output_with_phones_only.csv',
                        data=csv_only,
                        file_name='output_with_phones_only.csv',
                        mime='text/csv',
                        use_container_width=True,
                    )
                    st.download_button(
                        'Prenesi: output_phones_found.csv (name, phone, source)',
                        data=csv_min,
                        file_name='output_phones_found.csv',
                        mime='text/csv',
                        use_container_width=True,
                    )