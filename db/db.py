import streamlit as st
import psycopg2

def get_connection():
    return psycopg2.connect(st.secrets["postgresql://postgres:[YOUR-PASSWORD]@db.gddiloxvtcawylknvqnd.supabase.co:5432/postgres"])