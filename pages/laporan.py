import streamlit as st
import pandas as pd
from gsheets import load_data

def show_laporan_page():
    st.header("📈 Laporan Simpanan Bulanan")
    sheets = st.session_state["sheets"]
    
    # Load and standardize data
    gaji_data = load_data(sheets["gaji"])
    belanja_data = load_data(sheets["belanja"])
    
    # Standardize column names for gaji data
    gaji_columns = {
        'Tahun': ['Tahun', 'tahun', 'year'],
        'Bulan': ['Bulan', 'bulan', 'month'],
        'Nama': ['Nama', 'nama', 'name'],
        'Gaji Bersih': ['Gaji Bersih', 'gaji_bersih', 'Net Salary']
    }
    
    # Standardize column names for belanja data
    belanja_columns = {
        'Tahun': ['Tahun', 'tahun', 'year'],
        'Bulan': ['Bulan', 'bulan', 'month'],
        'Kategori': ['Kategori', 'kategori', 'category'],
        'Jumlah': ['Jumlah', 'jumlah', 'amount']
    }
    
    # Rename columns in gaji data
    for standard_name, possible_names in gaji_columns.items():
        for name in possible_names:
            if name in gaji_data.columns:
                gaji_data = gaji_data.rename(columns={name: standard_name})
                break
    
    # Rename columns in belanja data
    for standard_name, possible_names in belanja_columns.items():
        for name in possible_names:
            if name in belanja_data.columns:
                belanja_data = belanja_data.rename(columns={name: standard_name})
                break

    if gaji_data.empty or belanja_data.empty:
        st.warning("Sila isi data gaji dan belanja terlebih dahulu.")
        return

    with st.expander("🔍 Tapis Laporan"):
        tahun_list = sorted(set(gaji_data['Tahun'].dropna().unique()) | set(belanja_data['Tahun'].dropna().unique()))
        tahun_selected = st.selectbox("Tahun", tahun_list)
        nama_list = ["Semua"] + sorted(gaji_data['Nama'].dropna().unique())
        nama_selected = st.selectbox("Nama", nama_list)
        bulan_list = ["Semua"] + ["Jan", "Feb", "Mac", "Apr", "Mei", "Jun", "Jul", "Ogos", "Sep", "Okt", "Nov", "Dis"]
        bulan_selected = st.selectbox("Bulan", bulan_list)
        target_simpanan = st.number_input("🎯 Sasaran Simpanan Bulanan (RM)", 0.0, value=1000.0)

    # Filter data
    filtered_gaji = gaji_data[gaji_data['Tahun'] == tahun_selected]
    filtered_belanja = belanja_data[belanja_data['Tahun'] == tahun_selected]

    if nama_selected != "Semua":
        filtered_gaji = filtered_gaji[filtered_gaji['Nama'] == nama_selected]

    if bulan_selected != "Semua":
        bulan_map = {"Jan": "Jan", "Feb": "Feb", "Mac": "Mar", "Apr": "Apr", 
                    "Mei": "May", "Jun": "Jun", "Jul": "Jul", "Ogos": "Aug",
                    "Sep": "Sep", "Okt": "Oct", "Nov": "Nov", "Dis": "Dec"}
        bulan_value = bulan_map.get(bulan_selected, bulan_selected)
        filtered_gaji = filtered_gaji[filtered_gaji['Bulan'] == bulan_value]
        filtered_belanja = filtered_belanja[filtered_belanja['Bulan'] == bulan_value]

    # Grouping and calculations
    gaji_grouped = filtered_gaji.groupby(['Tahun', 'Bulan'])['Gaji Bersih'].sum()
    belanja_grouped = filtered_belanja.groupby(['Tahun', 'Bulan'])['Jumlah'].sum()

    laporan = pd.DataFrame({
        "Jumlah Gaji Bersih": gaji_grouped,
        "Jumlah Belanja": belanja_grouped
    }).fillna(0)
    
    laporan['Simpanan'] = laporan['Jumlah Gaji Bersih'] - laporan['Jumlah Belanja']
    laporan['Sasaran Simpanan'] = target_simpanan
    laporan['Beza dengan Sasaran'] = laporan['Simpanan'] - target_simpanan

    laporan = laporan.reset_index()
    laporan['BulanPenuh'] = laporan['Tahun'].astype(str) + "-" + laporan['Bulan']
    laporan = laporan.set_index('BulanPenuh')

    # Format display
    display_cols = ['Jumlah Gaji Bersih', 'Jumlah Belanja', 'Simpanan', 
                   'Sasaran Simpanan', 'Beza dengan Sasaran']
    formatted_laporan = laporan[display_cols].copy()
    formatted_laporan[display_cols] = formatted_laporan[display_cols].applymap(lambda x: f"RM {x:,.2f}")

    st.dataframe(formatted_laporan)
    st.caption("Data ditapis berdasarkan pilihan tahun, bulan dan nama di atas.")

    # Dynamic subtitle
    subtitle = f"{bulan_selected} {tahun_selected}" if bulan_selected != "Semua" else f"{tahun_selected} (Semua Bulan)"

    # Charts and metrics
    st.subheader(f"💰 Carta Simpanan Bar ({subtitle})")
    st.bar_chart(laporan[['Simpanan', 'Sasaran Simpanan']])

    st.subheader(f"📈 Carta Garisan Simpanan & Belanja ({subtitle})")
    st.line_chart(laporan[['Simpanan', 'Sasaran Simpanan', 'Jumlah Belanja']])

    if not filtered_belanja.empty:
        st.subheader(f"📊 Peratus Belanja Mengikut Kategori ({subtitle})")
        kategori_chart = filtered_belanja.groupby('Kategori')['Jumlah'].sum().sort_values(ascending=False)
        st.pyplot(kategori_chart.plot.pie(autopct='%1.1f%%', ylabel='', title='Perbelanjaan Ikut Kategori').figure)

    st.subheader(f"📋 Ringkasan ({subtitle})")
    total_gaji = filtered_gaji['Gaji Bersih'].sum()
    total_belanja = filtered_belanja['Jumlah'].sum()
    total_simpanan = total_gaji - total_belanja

    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Gaji", f"RM {total_gaji:,.2f}")
    col2.metric("Jumlah Belanja", f"RM {total_belanja:,.2f}")
    col3.metric("Jumlah Simpanan", f"RM {total_simpanan:,.2f}")