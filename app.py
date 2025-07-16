import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe

# === Login Setup ===
USERS = {
    "poknik": "1234",
    "isteri": "5678"
}

def show_login():
    st.set_page_config(page_title="Login", layout="centered")
    st.title("🔐 Login Sistem Kewangan Keluarga asal Pok Nik")

    username = st.text_input("Nama Pengguna")
    password = st.text_input("Kata Laluan", type="password")
    login_btn = st.button("Login")

    if login_btn:
        if USERS.get(username) == password:
            st.session_state["logged_in"] = True
            st.session_state["user"] = username
            st.success("Berjaya log masuk.")
            st.rerun()
        else:
            st.error("Nama pengguna atau kata laluan salah.")

# === Session check ===
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    show_login()
    st.stop()

# === Google Sheets Setup ===
def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/drive"]
    
    # Using Streamlit secrets
    creds_dict = {
        "type": st.secrets["gcp"]["type"],
        "project_id": st.secrets["gcp"]["project_id"],
        "private_key_id": st.secrets["gcp"]["private_key_id"],
        "private_key": st.secrets["gcp"]["private_key"].replace('\\n', '\n'),
        "client_email": st.secrets["gcp"]["client_email"],
        "client_id": st.secrets["gcp"]["client_id"],
        "auth_uri": st.secrets["gcp"]["auth_uri"],
        "token_uri": st.secrets["gcp"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp"]["client_x509_cert_url"]
    }
    
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(credentials)

# Initialize connection
try:
    gc = connect_to_gsheet()
    gaji_sheet = gc.open(st.secrets["sheets"]["gaji_sheet_name"]).sheet1
    belanja_sheet = gc.open(st.secrets["sheets"]["belanja_sheet_name"]).sheet1
except Exception as e:
    st.error(f"Gagal sambung ke Google Sheets: {e}")
    st.stop()

# Load data
def load_data(sheet):
    records = sheet.get_all_records()
    return pd.DataFrame(records)

gaji_data = load_data(gaji_sheet)
belanja_data = load_data(belanja_sheet)

# Save data
def save_data(sheet, df):
    sheet.clear()
    set_with_dataframe(sheet, df)

# === Streamlit UI ===
st.set_page_config(page_title="Sistem Kewangan Pok Nik", layout="wide")
st.title("📊 Sistem Kewangan Bulanan - Pok Nik")

# Sidebar Navigation
menu = st.sidebar.radio("Menu", ["Isi Gaji", "Catat Belanja", "Simpanan & Laporan"])

# ================= Isi Gaji =================
if menu == "Isi Gaji":
    st.header("📝 Isi Gaji Bulanan")

    if "edit_gaji" in st.session_state:
        selected_row = st.session_state["edit_gaji"]
        row_data = gaji_data.loc[selected_row]
    else:
        selected_row = None
        row_data = {}

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
            
            if selected_row is None:
                gaji_data = pd.concat([gaji_data, pd.DataFrame([new_row])], ignore_index=True)
            else:
                gaji_data.loc[selected_row] = new_row
                del st.session_state["edit_gaji"]
            
            save_data(gaji_sheet, gaji_data)
            st.success(f"Gaji untuk {nama} bulan {bulan} {tahun} disimpan.")
            st.rerun()

    if not gaji_data.empty:
        st.subheader("Rekod Gaji")
        edited_data = st.data_editor(gaji_data, num_rows="dynamic")
        
        if st.button("Simpan Perubahan"):
            save_data(gaji_sheet, edited_data)
            st.success("Perubahan disimpan!")
            st.rerun()

# ================= Catat Belanja =================
elif menu == "Catat Belanja":
    st.header("💸 Catat Perbelanjaan")

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
                              ["Makanan", "Bil", "Minyak", "Loan", "Lain-lain"],
                              index=["Makanan", "Bil", "Minyak", "Loan", "Lain-lain"].index(
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
            
            save_data(belanja_sheet, belanja_data)
            st.success("Belanja berjaya disimpan.")
            st.rerun()

    if not belanja_data.empty:
        st.subheader("Rekod Belanja")
        edited_data = st.data_editor(belanja_data, num_rows="dynamic")
        
        if st.button("Simpan Perubahan", key="save_belanja"):
            save_data(belanja_sheet, edited_data)
            st.success("Perubahan disimpan!")
            st.rerun()


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
            target_simpanan = st.number_input("🎯 Sasaran Simpanan Bulanan (RM)", 0.0, value=1000.0)

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
