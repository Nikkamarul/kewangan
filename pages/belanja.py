import streamlit as st
import pandas as pd
import datetime
from gsheets import load_data, save_data

def show_belanja_page():
    st.header("💸 Catat Perbelanjaan")
    sheets = st.session_state["sheets"]
    belanja_data = load_data(sheets["belanja"])
    
    # Standardize column names (modify according to your actual columns)
    column_mapping = {
        'Tarikh': 'tarikh',
        'Tahun': 'tahun',
        'Bulan': 'bulan',
        'Kategori': 'kategori',
        'Perkara': 'perkara',
        'Jumlah': 'jumlah'
    }
    belanja_data = belanja_data.rename(columns=column_mapping)

    # Edit existing entry
    if "edit_belanja" in st.session_state:
        selected_row = st.session_state["edit_belanja"]
        row_data = belanja_data.loc[selected_row].to_dict()
        is_edit_mode = True
    else:
        row_data = {}
        is_edit_mode = False

    with st.form("form_belanja"):
        tarikh = st.date_input("Tarikh", 
                             value=pd.to_datetime(row_data.get("tarikh", datetime.date.today())))
        kategori = st.selectbox("Kategori", 
                              ["Makanan", "Bil", "Minyak", "Loan", "Shopping", "Lain-lain"],
                              index=["Makanan", "Bil", "Minyak", "Loan", "Shopping", "Lain-lain"].index(
                                  row_data.get("kategori", "Makanan")))
        perkara = st.text_input("Perkara", value=row_data.get("perkara", ""))
        jumlah = st.number_input("Jumlah (RM)", min_value=0.0, 
                               value=float(row_data.get("jumlah", 0)))
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Simpan Belanja")
        with col2:
            if is_edit_mode:
                if st.form_submit_button("Batal Edit"):
                    del st.session_state["edit_belanja"]
                    st.rerun()

        if submitted:
            new_row = {
                "tarikh": tarikh,
                "tahun": tarikh.year,
                "bulan": tarikh.strftime('%b'),
                "kategori": kategori,
                "perkara": perkara,
                "jumlah": jumlah
            }
            
            if is_edit_mode:
                belanja_data.loc[selected_row] = new_row
                del st.session_state["edit_belanja"]
            else:
                belanja_data = pd.concat([belanja_data, pd.DataFrame([new_row])], ignore_index=True)
            
            save_data(sheets["belanja"], belanja_data)
            st.success("Belanja berjaya disimpan!")
            st.rerun()

    if not belanja_data.empty:
        st.subheader("Rekod Belanja")
        
        # Filter options
        unique_years = sorted(belanja_data["tahun"].unique(), reverse=True)
        unique_months = list(belanja_data["bulan"].unique())

        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox("Pilih Tahun", unique_years, index=0, key="year_filter")
        with col2:
            selected_month = st.selectbox("Pilih Bulan", unique_months, index=0, key="month_filter")

        # Apply filters
        filtered_data = belanja_data[
            (belanja_data["tahun"] == selected_year) &
            (belanja_data["bulan"] == selected_month)
        ].copy()

        # Display table header
        cols = st.columns([1,1,1,1,1,2])
        headers = ["Tarikh", "Kategori", "Perkara", "Jumlah (RM)", "Tindakan"]
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")
        st.divider()

        # Display each row with action buttons
        for idx, row in filtered_data.iterrows():
            cols = st.columns([1,1,1,1,1,2])
            
            # Display data
            cols[0].write(row["tarikh"].strftime('%Y-%m-%d') if isinstance(row["tarikh"], pd.Timestamp) else row["tarikh"])
            cols[1].write(row["kategori"])
            cols[2].write(row["perkara"])
            cols[3].write(f"RM {row['jumlah']:,.2f}")
            
            # Action buttons
            with cols[5]:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("✏️ Edit", key=f"edit_{idx}", use_container_width=True):
                        st.session_state["edit_belanja"] = idx
                        st.rerun()
                with btn_col2:
                    if st.button("🗑️ Padam", key=f"delete_{idx}", use_container_width=True):
                        belanja_data = belanja_data.drop(index=idx)
                        save_data(sheets["belanja"], belanja_data)
                        st.success("Rekod berjaya dipadam!")
                        st.rerun()
            
            st.divider()