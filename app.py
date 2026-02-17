from streamlit_gsheets import GSheetsConnection
import streamlit as st
import pandas as pd


df = pd.DataFrame(columns=['Date', 'Category', 'Amount', 'Notes'])


# Create the connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Read existing data
existing_data = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1VDWOVPBUMgveaFE_ugjCQVJSVO72MfFXbAowN-nUTeY/edit?usp=sharing")


# Function to add new data
if st.button("Save Expense"):
    # Log logic here
    conn.update(spreadsheet="https://docs.google.com/spreadsheets/d/1VDWOVPBUMgveaFE_ugjCQVJSVO72MfFXbAowN-nUTeY/edit?usp=sharing", data=df)
    st.success("Data saved to Google Sheets!")
