import streamlit as st
from auth import check_auth
from utils import setup_page

# Check authentication
if not check_auth():
    from auth import show_login
    show_login()
    st.stop()

# Hide Streamlit's native navigation
st.markdown("""
<style>
    /* Hide hamburger menu */
    [data-testid="collapsedControl"] {
        display: none;
    }
    /* Hide the default sidebar navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    /* Adjust sidebar width */
    section[data-testid="stSidebar"] {
        width: 200px !important;
    }
</style>
""", unsafe_allow_html=True)

# Main app
setup_page("📊 Sistem Kewangan keluarga")

# Sidebar Navigation
menu = st.sidebar.radio("Menu", ["Isi Gaji", "Catat Belanja", "Simpanan & Laporan"])

if menu == "Isi Gaji":
    from pages.gaji import show_gaji_page
    show_gaji_page()
elif menu == "Catat Belanja":
    from pages.belanja import show_belanja_page
    show_belanja_page()
elif menu == "Simpanan & Laporan":
    from pages.laporan import show_laporan_page
    show_laporan_page()