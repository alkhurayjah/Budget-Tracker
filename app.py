# import streamlit as st
# from streamlit_gsheets import GSheetsConnection
# import pandas as pd

# # 1. Setup Connection
# # Make sure your .streamlit/secrets.toml is configured if this is a private sheet!
# conn = st.connection("gsheets", type=GSheetsConnection)

# # 2. Clean URL (Remove the /edit?usp=sharing part)
# URL = "https://docs.google.com/spreadsheets/d/1VDWOVPBUMgveaFE_ugjCQVJSVO72MfFXbAowN-nUTeY/edit?usp=sharing"

# # 3. Read existing data safely
# try:
#     existing_data = conn.read(spreadsheet=URL, usecols=[0, 1, 2, 3])
#     st.subheader("Current Budget Data")
#     st.dataframe(existing_data)
# except Exception as e:
#     st.error(f"Error reading sheet: {e}")
#     existing_data = pd.DataFrame(columns=['Date', 'Category', 'Amount', 'Notes'])

# # 4. Input Fields (You need these so 'df' isn't empty!)
# st.divider()
# st.subheader("Add New Expense")
# with st.form("entry_form"):
#     date = st.date_input("Date")
#     category = st.selectbox("Category", ["Food", "Rent", "Utilities", "Fun"])
#     amount = st.number_input("Amount", min_value=0.0, step=0.01)
#     notes = st.text_input("Notes")
    
#     submit = st.form_submit_button("Save Expense")

# # 5. Update Logic
# if submit:
#     # Create a new row
#     new_data = pd.DataFrame([{
#         "Date": str(date),
#         "Category": category,
#         "Amount": amount,
#         "Notes": notes
#     }])
    
#     # Add new row to existing data
#     updated_df = pd.concat([existing_data, new_data], ignore_index=True)
    
#     # Update the Google Sheet
#     conn.update(spreadsheet=URL, data=updated_df)
#     st.success("Data saved successfully!")
#     st.rerun() # Refresh to show the new data in the table above

import streamlit as st
from medical_gsheets import GSheetsConnection

# App Title
st.title("Google Sheets Read/Write Demo")

# Create a connection object
conn = st.connection("gsheets", type=GSheetsConnection)

# 1. READ Data
# Replace the URL below with your actual Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1VDWOVPBUMgveaFE_ugjCQVJSVO72MfFXbAowN-nUTeY/edit?usp=sharing"

df = conn.read(spreadsheet=SHEET_URL, usecols=[0, 1]) # Adjust columns as needed

st.subheader("Current Data")
st.dataframe(df)

# 2. WRITE Data
st.subheader("Add New Entry")

with st.form("entry_form"):
    name = st.text_input("Name")
    message = st.text_area("Message")
    submit = st.form_submit_button("Submit to Sheet")

    if submit:
        if name and message:
            # Create a new row
            new_data = {"Name": name, "Message": message}
            
            # Append to the dataframe and update the sheet
            updated_df = df.append(new_data, ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, data=updated_df)
            
            st.success("Data successfully written!")
            st.rerun() # Refresh to show new data
        else:
            st.warning("Please fill out both fields.")

