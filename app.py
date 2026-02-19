""""
for running the app, use the command:
    streamlit run app.py

for sop runing:
      contrlo + c ,

"""""
import streamlit as st
from db.db import create_user, authenticate_user


st.image("assets/logo.png", width=200)
st.title("Budget Tracker")


tab1, tab2 = st.tabs(["Login", "Sign Up"])

# LOGIN
with tab1:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.success("Logged in successfully ✅")
            st.session_state["user_id"] = user[0]
        else:
            st.error("Invalid credentials ❌")

# SIGNUP
with tab2:
    st.subheader("Create Account")
    new_user = st.text_input("Username", key="su1")
    phone = st.text_input("Phone", key="su2")
    new_pass = st.text_input("Password", type="password", key="su3")
    question = st.text_input("Security Question", key="su4")
    answer = st.text_input("Security Answer", key="su5")

    if st.button("Sign Up"):
        try:
            create_user(new_user, phone, new_pass, question, answer)
            st.success("Account created 🎉")
        except Exception as e:
            st.error("User already exists or error occurred")
