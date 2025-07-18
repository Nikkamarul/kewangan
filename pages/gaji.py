import streamlit as st
import pandas as pd
import datetime
from gsheets import load_data, save_data

def show_gaji_page():
    st.header("📝 Isi Gaji Bulanan")
    
    # Load data from Google Sheets
    gaji_data = load_data(st.session_state.sheets["gaji"])
    
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
                              value=int(row_data.get("Tahun", datetime.datetime.today().year)))
        nama = st.selectbox("Nama", ["Pok Nik", "Isteri"], 
                          index=0 if row_data.get("Nama") != "Isteri" else 1)
        bulan = st.selectbox("Bulan", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                          index=["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(
                                    row_data.get("Bulan", "Jan")))
        gaji_pokok = st.number_input("Gaji Pokok", min_value=0.0, 
                                    value=float(row_data.get("Gaji Pokok", 0)))
        elaun = st.number_input("Elaun", min_value=0.0, 
                              value=float(row_data.get("Elaun", 0)))
        ot = st.number_input("OT", min_value=0.0, 
                           value=float(row_data.get("OT", 0)))
        potongan = st.number_input("Potongan", min_value=0.0, 
                                 value=float(row_data.get("Potongan", 0)))
        
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
                "Tahun": tahun,
                "Bulan": bulan,
                "Nama": nama,
                "Gaji Pokok": gaji_pokok,
                "Elaun": elaun,
                "OT": ot,
                "Potongan": potongan,
                "Gaji Bersih": bersih
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
        unique_years = sorted(gaji_data["Tahun"].unique(), reverse=True)
        unique_months = list(gaji_data["Bulan"].unique())

        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox("Pilih Tahun", unique_years, index=0, key="year_filter")
        with col2:
            selected_month = st.selectbox("Pilih Bulan", unique_months, index=0, key="month_filter")

        # Apply filters
        filtered_data = gaji_data[
            (gaji_data["Tahun"] == selected_year) & 
            (gaji_data["Bulan"] == selected_month)
        ].copy()

        # Add action buttons
        filtered_data["Action"] = ["🗑️|✏️"] * len(filtered_data)
        edited_data = st.data_editor(
            filtered_data.drop(columns=["Action"]),
            disabled=list(filtered_data.columns),
            hide_index=True
        )

        # Handle actions
        for i, row in filtered_data.iterrows():
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Padam", key=f"delete_{i}"):
                    gaji_data = gaji_data.drop(index=i)
                    save_data(st.session_state.sheets["gaji"], gaji_data)
                    st.success("Rekod berjaya dipadam!")
                    st.rerun()
            with col2:
                if st.button(f"Edit", key=f"edit_{i}"):
                    st.session_state["edit_gaji"] = i
                    st.rerun()