import psycopg2
import streamlit as st
def get_connection():
    return psycopg2.connect(st.secrets["postgresql://postgres.gddiloxvtcawylknvqnd:2M&fQw/2PDa#Q#C@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"])