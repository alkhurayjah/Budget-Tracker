import streamlit as st

""""
for running the app, use the command:
    streamlit run app.py

for sop runing:
      contrlo + c

"""""
st.title("Budget Tracker 🚀")
st.write("Streamlit project is ready")
import streamlit as st
from db.db import get_connection

st.title("Supabase Test")

if st.button("Test DB"):
    try:
        conn = get_connection()
        conn.cursor().execute("SELECT 1;")
        st.success("Connected to Supabase ✅")
        conn.close()
    except Exception as e:
        st.error("Connection failed ❌")
        st.code(str(e))
