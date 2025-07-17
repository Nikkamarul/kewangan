import streamlit as st

def check_auth():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    return st.session_state["logged_in"]

def show_login():
    st.set_page_config(page_title="Login", layout="centered")
    st.title("🔐 Login Sistem Kewangan Keluarga Pok Nik")

    USERS = st.secrets["users"]
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