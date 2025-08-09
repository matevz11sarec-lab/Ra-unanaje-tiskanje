import io
import tempfile
from typing import Optional

import pandas as pd
import streamlit as st

from core.enrich import run_enrichment
from core.agency import run_agency_enrichment
from utils.io import read_input_csv

st.set_page_config(page_title='Enricher (bizi.si + companywall.si)', layout='centered')
st.title('Enricher')

mode_tabs = st.tabs(["Tiskarska podjetja", "Podjetja za agencijo"])

# Tab 1: Tiskarska podjetja (phone enrichment)
with mode_tabs[0]:
    st.subheader('Tiskarska podjetja: iskanje telefonskih številk')
    st.markdown('Naložite CSV datoteko z obveznim stolpcem `name` in opcijskim `bizi_url`.')

    uploaded_csv = st.file_uploader('Vhodni CSV (UTF-8)', type=['csv'], key='csv1')
    auth_state_file = st.file_uploader('auth_state.json (neobvezno)', type=['json'], key='auth1')

    col1, col2 = st.columns(2)
    with col1:
        min_delay = st.number_input('Min. zamik (sekunde)', min_value=0.5, max_value=10.0, value=1.5, step=0.1, key='min1')
    with col2:
        max_delay = st.number_input('Maks. zamik (sekunde)', min_value=0.5, max_value=15.0, value=3.5, step=0.1, key='max1')

    headful = st.checkbox('Prikaži brskalnik (headful)', value=False, key='head1')
    run_btn = st.button('Zaženi obogatitev', type='primary', use_container_width=True, key='run1')

    progress_placeholder = st.empty()
    log_placeholder = st.empty()

    if run_btn:
        if uploaded_csv is None:
            st.error('Najprej naložite CSV datoteko.')
        elif min_delay > max_delay:
            st.error('Min. zamik ne sme biti večji od maks. zamika.')
        else:
            try:
                df_input = read_input_csv(uploaded_csv)
            except Exception as exc:  # noqa: BLE001
                st.error(f'Napaka pri branju CSV: {exc}')
            else:
                auth_state_path: Optional[str] = None
                if auth_state_file is not None:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tf:
                        tf.write(auth_state_file.read())
                        auth_state_path = tf.name

                progress_bar = st.progress(0)
                logs = []

                def progress_cb(current: int, total: int, name: str, message: str) -> None:
                    pct = int(current / max(total, 1) * 100)
                    progress_bar.progress(pct)
                    logs.append(f'[{current}/{total}] {name} -> {message}')
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

                        st.download_button('Prenesi: output_with_phones.csv', data=csv_all, file_name='output_with_phones.csv', mime='text/csv', use_container_width=True)
                        st.download_button('Prenesi: output_with_phones_only.csv', data=csv_only, file_name='output_with_phones_only.csv', mime='text/csv', use_container_width=True)
                        st.download_button('Prenesi: output_phones_found.csv (name, phone, source)', data=csv_min, file_name='output_phones_found.csv', mime='text/csv', use_container_width=True)

# Tab 2: Podjetja za agencijo (website-first)
with mode_tabs[1]:
    st.subheader('Podjetja za agencijo: podjetja brez spletne strani + telefon')
    st.markdown('Najprej preveri, če podjetje že ima spletno stran; če je nima, poišče telefonsko številko.')

    uploaded_csv2 = st.file_uploader('Vhodni CSV (UTF-8)', type=['csv'], key='csv2')
    auth_state_file2 = st.file_uploader('auth_state.json (neobvezno)', type=['json'], key='auth2')

    col3, col4 = st.columns(2)
    with col3:
        min_delay2 = st.number_input('Min. zamik (sekunde)', min_value=0.5, max_value=10.0, value=1.5, step=0.1, key='min2')
    with col4:
        max_delay2 = st.number_input('Maks. zamik (sekunde)', min_value=0.5, max_value=15.0, value=3.5, step=0.1, key='max2')

    headful2 = st.checkbox('Prikaži brskalnik (headful)', value=False, key='head2')
    always_phone = st.checkbox('Vedno poišči telefonsko številko (tudi če obstaja spletna stran)', value=False, key='always_phone')
    run_btn2 = st.button('Zaženi preverjanje spletne strani + telefon', type='primary', use_container_width=True, key='run2')

    progress_placeholder2 = st.empty()
    log_placeholder2 = st.empty()

    if run_btn2:
        if uploaded_csv2 is None:
            st.error('Najprej naložite CSV datoteko.')
        elif min_delay2 > max_delay2:
            st.error('Min. zamik ne sme biti večji od maks. zamika.')
        else:
            try:
                df_input2 = read_input_csv(uploaded_csv2)
            except Exception as exc:  # noqa: BLE001
                st.error(f'Napaka pri branju CSV: {exc}')
            else:
                auth_state_path2: Optional[str] = None
                if auth_state_file2 is not None:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tf:
                        tf.write(auth_state_file2.read())
                        auth_state_path2 = tf.name

                progress_bar2 = st.progress(0)
                logs2 = []

                def progress_cb2(current: int, total: int, name: str, message: str) -> None:
                    pct = int(current / max(total, 1) * 100)
                    progress_bar2.progress(pct)
                    logs2.append(f'[{current}/{total}] {name} -> {message}')
                    log_placeholder2.write('\n'.join(logs2[-10:]))

                with st.spinner('Izvajam...'):
                    try:
                        df_res2, found_count2, total2 = run_agency_enrichment(
                            df=df_input2,
                            headful=headful2,
                            auth_state=auth_state_path2,
                            min_delay=float(min_delay2),
                            max_delay=float(max_delay2),
                            progress_cb=progress_cb2,
                            always_search_phone=always_phone,
                        )
                    except Exception as exc:  # noqa: BLE001
                        st.error(f'Napaka: {exc}')
                    else:
                        success_pct2 = (found_count2 / total2 * 100.0) if total2 else 0.0
                        st.success(f'Končano. Najdenih telefonov (pri podjetjih brez spletne strani): {found_count2}/{total2} ({success_pct2:.1f}%).')

                        # Downloads: full, only without website, and minimal phones for no-website
                        csv_all2 = df_res2.to_csv(index=False).encode('utf-8')
                        df_no_site = df_res2[df_res2['website_status'] == 'nima spletne strani'].copy()
                        csv_no_site = df_no_site.to_csv(index=False).encode('utf-8')

                        try:
                            df_min2 = df_no_site[df_no_site['phone'].astype(str).str.strip() != ''][['name', 'phone', 'source']].copy()
                            csv_min2 = df_min2.to_csv(index=False).encode('utf-8')
                        except Exception:
                            df_min2 = pd.DataFrame(columns=['name', 'phone', 'source'])
                            csv_min2 = df_min2.to_csv(index=False).encode('utf-8')

                        st.download_button('Prenesi: agency_all.csv', data=csv_all2, file_name='agency_all.csv', mime='text/csv', use_container_width=True)
                        st.download_button('Prenesi: agency_no_website_only.csv', data=csv_no_site, file_name='agency_no_website_only.csv', mime='text/csv', use_container_width=True)
                        st.download_button('Prenesi: agency_no_website_phones_found.csv (name, phone, source)', data=csv_min2, file_name='agency_no_website_phones_found.csv', mime='text/csv', use_container_width=True)