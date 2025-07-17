import streamlit as st

def setup_page(title):
    st.set_page_config(page_title="Sistem Kewangan Keluarga", layout="wide")
    st.title(title)
    
    # Initialize sheets connection if not already done
    if "sheets" not in st.session_state:
        from gsheets import get_sheets
        st.session_state["sheets"] = get_sheets()