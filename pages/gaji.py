import streamlit as st
import pandas as pd
import datetime
from gsheets import load_data, save_data

def show_gaji_page():
    st.header("📝 Isi Gaji Bulanan")
    
    # Load data from Google Sheets
    gaji_data = load_data(st.session_state.sheets["gaji"])
    
    # Standardize column names (modify according to your actual columns)
    column_mapping = {
        'Tahun': 'tahun',
        'Bulan': 'bulan',
        'Nama': 'nama',
        'Gaji Pokok': 'gaji_pokok',
        'Elaun': 'elaun',
        'OT': 'ot',
        'Potongan': 'potongan',
        'Gaji Bersih': 'gaji_bersih'
    }
    gaji_data = gaji_data.rename(columns=column_mapping)

    # Edit existing entry
    if "edit_gaji" in st.session_state:
        selected_row = st.session_state["edit_gaji"]
        row_data = gaji_data.loc[selected_row].to_dict()
        is_edit_mode = True
    else:
        row_data = {}
        is_edit_mode = False

    with st.form("form_gaji"):
        tahun = st.number_input("Tahun", min_value=2020, max_value=2100, 
                              value=int(row_data.get("tahun", datetime.datetime.today().year)))
        nama = st.selectbox("Nama", ["Pok Nik", "Isteri"], 
                          index=0 if row_data.get("nama") != "Isteri" else 1)
        bulan = st.selectbox("Bulan", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                          index=["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(
                                    row_data.get("bulan", "Jan")))
        gaji_pokok = st.number_input("Gaji Pokok", min_value=0.0, 
                                    value=float(row_data.get("gaji_pokok", 0)))
        elaun = st.number_input("Elaun", min_value=0.0, 
                              value=float(row_data.get("elaun", 0)))
        ot = st.number_input("OT", min_value=0.0, 
                           value=float(row_data.get("ot", 0)))
        potongan = st.number_input("Potongan", min_value=0.0, 
                                 value=float(row_data.get("potongan", 0)))
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Simpan Gaji")
        with col2:
            if is_edit_mode:
                if st.form_submit_button("Batal Edit"):
                    del st.session_state["edit_gaji"]
                    st.rerun()

        if submitted:
            bersih = gaji_pokok + elaun + ot - potongan
            new_row = {
                "tahun": tahun,
                "bulan": bulan,
                "nama": nama,
                "gaji_pokok": gaji_pokok,
                "elaun": elaun,
                "ot": ot,
                "potongan": potongan,
                "gaji_bersih": bersih
            }
            
            if is_edit_mode:
                gaji_data.loc[selected_row] = new_row
                del st.session_state["edit_gaji"]
            else:
                gaji_data = pd.concat([gaji_data, pd.DataFrame([new_row])], ignore_index=True)
            
            save_data(st.session_state.sheets["gaji"], gaji_data)
            st.success("Data gaji berjaya disimpan!")
            st.rerun()

    if not gaji_data.empty:
        st.subheader("Rekod Gaji")
        
        # Filter options
        unique_years = sorted(gaji_data["tahun"].unique(), reverse=True)
        unique_months = list(gaji_data["bulan"].unique())

        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox("Pilih Tahun", unique_years, index=0, key="year_filter")
        with col2:
            selected_month = st.selectbox("Pilih Bulan", unique_months, index=0, key="month_filter")

        # Apply filters
        filtered_data = gaji_data[
            (gaji_data["tahun"] == selected_year) & 
            (gaji_data["bulan"] == selected_month)
        ].copy()

        # Display table header
        cols = st.columns([1,1,1,1,1,1,1,1,2])
        headers = ["Tahun", "Bulan", "Nama", "Gaji Pokok", "Elaun", "OT", "Potongan", "Gaji Bersih", "Tindakan"]
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")
        st.divider()

        # Display each row with action buttons
        for idx, row in filtered_data.iterrows():
            cols = st.columns([1,1,1,1,1,1,1,1,2])
            
            # Display data
            cols[0].write(row["tahun"])
            cols[1].write(row["bulan"])
            cols[2].write(row["nama"])
            cols[3].write(f"RM {row['gaji_pokok']:,.2f}")
            cols[4].write(f"RM {row['elaun']:,.2f}")
            cols[5].write(f"RM {row['ot']:,.2f}")
            cols[6].write(f"RM {row['potongan']:,.2f}")
            cols[7].write(f"RM {row['gaji_bersih']:,.2f}")
            
            # Action buttons
            with cols[8]:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("✏️ Edit", key=f"edit_{idx}", use_container_width=True):
                        st.session_state["edit_gaji"] = idx
                        st.rerun()
                with btn_col2:
                    if st.button("🗑️ Padam", key=f"delete_{idx}", use_container_width=True):
                        gaji_data = gaji_data.drop(index=idx)
                        save_data(st.session_state.sheets["gaji"], gaji_data)
                        st.success("Rekod berjaya dipadam!")
                        st.rerun()
            
            st.divider()