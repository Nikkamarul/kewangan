import streamlit as st
import pandas as pd
import datetime
from gsheets import load_data, save_data

def show_belanja_page():
    st.header("💸 Catat Perbelanjaan")
    sheets = st.session_state["sheets"]
    belanja_data = load_data(sheets["belanja"])

    if "edit_belanja" in st.session_state:
        selected_row = st.session_state["edit_belanja"]
        row_data = belanja_data.loc[selected_row]
    else:
        selected_row = None
        row_data = {}

    with st.form("form_belanja"):
        tarikh = st.date_input("Tarikh", 
                             value=pd.to_datetime(row_data.get("Tarikh", datetime.date.today())))
        kategori = st.selectbox("Kategori", 
                              ["Makanan", "Bil", "Minyak", "Loan", "Shopping", "Lain-lain"],
                              index=["Makanan", "Bil", "Minyak", "Loan", "Shopping", "Lain-lain"].index(
                                  row_data.get("Kategori", "Makanan")))
        perkara = st.text_input("Perkara", value=row_data.get("Perkara", ""))
        jumlah = st.number_input("Jumlah (RM)", min_value=0.0, 
                               value=float(row_data.get("Jumlah", 0)))
        submitted = st.form_submit_button("Simpan Belanja")

        if submitted:
            new_row = {
                "Tarikh": tarikh,
                "Tahun": tarikh.year,
                "Bulan": tarikh.strftime('%b'),
                "Kategori": kategori,
                "Perkara": perkara,
                "Jumlah": jumlah
            }
            
            if selected_row is None:
                belanja_data = pd.concat([belanja_data, pd.DataFrame([new_row])], ignore_index=True)
            else:
                belanja_data.loc[selected_row] = new_row
                del st.session_state["edit_belanja"]
            
            save_data(sheets["belanja"], belanja_data)
            st.success("Belanja berjaya disimpan.")
            st.rerun()

    if not belanja_data.empty:
        st.subheader("Rekod Belanja")
        
        unique_years = sorted(belanja_data["Tahun"].unique(), reverse=True)
        unique_months = list(belanja_data["Bulan"].unique())

        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox("Pilih Tahun", unique_years, index=0)
        with col2:
            selected_month = st.selectbox("Pilih Bulan", unique_months, index=0)

        filtered_data = belanja_data[
            (belanja_data["Tahun"] == selected_year) &
            (belanja_data["Bulan"] == selected_month)
        ]

        edited_data = st.data_editor(filtered_data, num_rows="dynamic")

        if st.button("Simpan Perubahan", key="save_belanja"):
            for i, row in filtered_data.iterrows():
                belanja_data.loc[i] = row

            save_data(sheets["belanja"], belanja_data)
            st.success("Perubahan disimpan!")
            st.rerun()