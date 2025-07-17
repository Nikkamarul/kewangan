import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe
import streamlit as st

def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/drive"]
    
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

def get_sheets():
    try:
        gc = connect_to_gsheet()
        return {
            "gaji": gc.open(st.secrets["sheets"]["gaji_sheet_name"]).sheet1,
            "belanja": gc.open(st.secrets["sheets"]["belanja_sheet_name"]).sheet1
        }
    except Exception as e:
        st.error(f"Gagal sambung ke Google Sheets: {e}")
        st.stop()

def load_data(sheet):
    records = sheet.get_all_records()
    return pd.DataFrame(records)

def save_data(sheet, df):
    sheet.clear()
    set_with_dataframe(sheet, df)