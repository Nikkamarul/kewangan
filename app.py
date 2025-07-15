import streamlit as st
import pandas as pd
import datetime
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from google.oauth2.service_account import Credentials

# ===== Login Setup =====
USERS = {
    "poknik": "1234",
    "isteri": "5678"
}

def show_login():
    st.set_page_config(page_title="Login", layout="centered")
    st.title("🔐 Login Sistem Kewangan Pok Nik")
    username = st.text_input("Nama Pengguna")
    password = st.text_input("Kata Laluan", type="password")
    if st.button("Login"):
        if USERS.get(username) == password:
            st.session_state["logged_in"] = True
            st.session_state["user"] = username
            st.success("Berjaya log masuk.")
            st.rerun()
        else:
            st.error("Nama pengguna atau kata laluan salah.")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if not st.session_state["logged_in"]:
    show_login()
    st.stop()

# ===== Google Sheets Setup =====
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)
client = gspread.authorize(credentials)

GAJI_SHEET = "data_gaji"
BELANJA_SHEET = "data_belanja"

# ===== Fungsi cipta sheet jika tiada =====
def init_sheet(sheet_name, columns):
    try:
        sh = client.open(sheet_name)
        ws = sh.sheet1
        if ws.row_count < 2:
            ws.append_row(columns)
    except gspread.exceptions.SpreadsheetNotFound:
        sh = client.create(sheet_name)
        ws = sh.sheet1
        ws.append_row(columns)
        try:
            sh.share(
                st.secrets["gcp_service_account"]["client_email"],
                perm_type='user',
                role='writer'
            )
        except Exception as e:
            st.error(f"Ralat ketika share fail: {e}")
        st.success(f"Google Sheet '{sheet_name}' telah dicipta.")
        st.write(f"[Buka Sheet ini]({sh.url})")

# Panggil init
init_sheet(GAJI_SHEET, ["Tahun", "Bulan", "Nama", "Gaji Pokok", "Elaun", "OT", "Potongan", "Gaji Bersih"])
init_sheet(BELANJA_SHEET, ["Tarikh", "Tahun", "Bulan", "Kategori", "Perkara", "Jumlah"])

# ===== Load & Save Data =====
def load_data(sheet_name):
    ws = client.open(sheet_name).sheet1
    df = get_as_dataframe(ws, evaluate_formulas=True).dropna(how='all')
    return df

def save_data(sheet_name, df):
    ws = client.open(sheet_name).sheet1
    ws.clear()
    set_with_dataframe(ws, df)

gaji_data = load_data(GAJI_SHEET)
belanja_data = load_data(BELANJA_SHEET)

# ===== UI Start =====
st.set_page_config(page_title="Sistem Kewangan Pok Nik", layout="wide")
st.title("📊 Sistem Kewangan Bulanan - Pok Nik")

menu = st.sidebar.radio("Menu", ["Isi Gaji", "Catat Belanja", "Simpanan & Laporan"])

# ===== Isi Gaji =====
if menu == "Isi Gaji":
    st.header("📝 Isi Gaji Bulanan")
    selected_row = st.query_params.get("edit_gaji", ["Tambah Baru"])[0]
    if selected_row != "Tambah Baru":
        row_data = gaji_data.loc[int(selected_row)]
    else:
        row_data = {}

    with st.form("form_gaji"):
        tahun = st.number_input("Tahun", 2020, 2100, int(row_data.get("Tahun", datetime.datetime.today().year)))
        nama = st.selectbox("Nama", ["Pok Nik", "Isteri"], index=0 if row_data.get("Nama") != "Isteri" else 1)
        bulan = st.selectbox("Bulan", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], index=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(row_data.get("Bulan", "Jan")))
        gaji_pokok = st.number_input("Gaji Pokok", min_value=0.0, value=float(row_data.get("Gaji Pokok", 0)))
        elaun = st.number_input("Elaun", min_value=0.0, value=float(row_data.get("Elaun", 0)))
        ot = st.number_input("OT", min_value=0.0, value=float(row_data.get("OT", 0)))
        potongan = st.number_input("Potongan", min_value=0.0, value=float(row_data.get("Potongan", 0)))
        submitted = st.form_submit_button("Simpan Gaji")

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
            if selected_row == "Tambah Baru":
                gaji_data = pd.concat([gaji_data, pd.DataFrame([new_row])], ignore_index=True)
            else:
                for key in new_row:
                    gaji_data.at[int(selected_row), key] = new_row[key]
                del st.query_params["edit_gaji"]
            save_data(GAJI_SHEET, gaji_data)
            st.success(f"Gaji disimpan.")
            st.rerun()

    if not gaji_data.empty:
        st.subheader("Rekod Gaji")
        for i, row in gaji_data.iterrows():
            cols = st.columns(len(row) + 1)
            for j, value in enumerate(row.values):
                cols[j].write(value)
            with cols[-1]:
                if st.button("Kemaskini", key=f"edit_gaji_{i}"):
                    st.query_params["edit_gaji"] = i
                    st.rerun()
                if st.button("Padam", key=f"delete_gaji_{i}"):
                    gaji_data = gaji_data.drop(index=i).reset_index(drop=True)
                    save_data(GAJI_SHEET, gaji_data)
                    st.rerun()

# ===== Catat Belanja =====
elif menu == "Catat Belanja":
    st.header("💸 Catat Perbelanjaan")
    selected_row = st.query_params.get("edit_belanja", ["Tambah Baru"])[0]
    if selected_row != "Tambah Baru":
        row_data = belanja_data.loc[int(selected_row)]
    else:
        row_data = {}

    with st.form("form_belanja"):
        tarikh = st.date_input("Tarikh", value=pd.to_datetime(row_data.get("Tarikh", datetime.date.today())))
        tahun = tarikh.year
        bulan = tarikh.strftime('%b')
        kategori = st.selectbox("Kategori", ["Makanan", "Bil", "Minyak", "Loan", "Lain-lain"], index=["Makanan", "Bil", "Minyak", "Loan", "Lain-lain"].index(row_data.get("Kategori", "Makanan")))
        perkara = st.text_input("Perkara", value=row_data.get("Perkara", ""))
        jumlah = st.number_input("Jumlah (RM)", min_value=0.0, value=float(row_data.get("Jumlah", 0)))
        submitted = st.form_submit_button("Simpan Belanja")

        if submitted:
            new_row = {
                "Tarikh": tarikh,
                "Tahun": tahun,
                "Bulan": bulan,
                "Kategori": kategori,
                "Perkara": perkara,
                "Jumlah": jumlah
            }
            if selected_row == "Tambah Baru":
                belanja_data = pd.concat([belanja_data, pd.DataFrame([new_row])], ignore_index=True)
            else:
                for key in new_row:
                    belanja_data.at[int(selected_row), key] = new_row[key]
                del st.query_params["edit_belanja"]
            save_data(BELANJA_SHEET, belanja_data)
            st.success("Belanja berjaya disimpan.")
            st.rerun()

    if not belanja_data.empty:
        st.subheader("Rekod Belanja")
        for i, row in belanja_data.iterrows():
            cols = st.columns(len(row) + 1)
            for j, value in enumerate(row.values):
                cols[j].write(value)
            with cols[-1]:
                if st.button("Kemaskini", key=f"edit_belanja_{i}"):
                    st.query_params["edit_belanja"] = i
                    st.rerun()
                if st.button("Padam", key=f"delete_belanja_{i}"):
                    belanja_data = belanja_data.drop(index=i).reset_index(drop=True)
                    save_data(BELANJA_SHEET, belanja_data)
                    st.rerun()

# ===== Simpanan & Laporan =====
elif menu == "Simpanan & Laporan":
    st.header("📈 Laporan Simpanan Bulanan")
    if gaji_data.empty or belanja_data.empty:
        st.warning("Sila isi data gaji dan belanja terlebih dahulu.")
    else:
        with st.expander("🔍 Tapis Laporan"):
            tahun_list = sorted(set(gaji_data['Tahun'].dropna().unique()) | set(belanja_data['Tahun'].dropna().unique()))
            tahun_selected = st.selectbox("Tahun", tahun_list)

            nama_list = ["Semua"] + sorted(gaji_data['Nama'].dropna().unique())
            nama_selected = st.selectbox("Nama", nama_list)

            bulan_list = ["Semua"] + ["Jan", "Feb", "Mac", "Apr", "Mei", "Jun", "Jul", "Ogos", "Sep", "Okt", "Nov", "Dis"]
            bulan_selected = st.selectbox("Bulan", bulan_list)

            target_simpanan = st.number_input("🎯 Sasaran Simpanan Bulanan (RM)", min_value=0.0, value=1000.0)

        filtered_gaji = gaji_data[gaji_data['Tahun'] == tahun_selected]
        filtered_belanja = belanja_data[belanja_data['Tahun'] == tahun_selected]

        if nama_selected != "Semua":
            filtered_gaji = filtered_gaji[filtered_gaji['Nama'] == nama_selected]

        if bulan_selected != "Semua":
            filtered_gaji = filtered_gaji[filtered_gaji['Bulan'] == bulan_selected]
            filtered_belanja = filtered_belanja[filtered_belanja['Bulan'] == bulan_selected]

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

        st.dataframe(laporan)

        st.subheader("💰 Carta Simpanan")
        st.bar_chart(laporan[['Simpanan', 'Sasaran Simpanan']])

        st.subheader("📊 Peratus Belanja Mengikut Kategori")
        kategori_chart = filtered_belanja.groupby('Kategori')['Jumlah'].sum()
        st.pyplot(kategori_chart.plot.pie(autopct='%1.1f%%', ylabel='', title='Perbelanjaan Ikut Kategori').figure)

        st.subheader("📋 Ringkasan Tahunan")
        total_gaji = filtered_gaji['Gaji Bersih'].sum()
        total_belanja = filtered_belanja['Jumlah'].sum()
        total_simpanan = total_gaji - total_belanja

        col1, col2, col3 = st.columns(3)
        col1.metric("Jumlah Gaji", f"RM {total_gaji:,.2f}")
        col2.metric("Jumlah Belanja", f"RM {total_belanja:,.2f}")
        col3.metric("Jumlah Simpanan", f"RM {total_simpanan:,.2f}")
