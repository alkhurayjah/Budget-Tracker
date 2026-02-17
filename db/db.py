import psycopg2
import streamlit as st

def get_connection():
    return psycopg2.connect(st.secrets["postgresql://postgres.gddiloxvtcawylknvqnd:[YOUR-PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"])
