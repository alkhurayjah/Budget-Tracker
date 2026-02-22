""""
for running the app, use the command:
    streamlit run app.py

for sop runing:
      contrlo + c ,

"""""

import streamlit as st
from db.db import (
    create_user,
    authenticate_user,
    get_security_question,
    verify_security_answer,
    update_password,
    verify_user_phone 
)
SECURITY_QUESTIONS = [
    "What is your favorite color?",
    "What is the name of your first school?",
    "What city were you born in?"
]


st.image("assets/logo.png", width=200)
st.title("Budget Tracker")


tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Forgot Password"])

# LOGIN
with tab1:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.success("Logged in successfully ✅")
            st.session_state["user_id"] = str(user[0])
            st.rerun()
        else:
            st.error("Invalid credentials ❌")

# SIGNUP
with tab2:
    st.subheader("Create Account")
    new_user = st.text_input("Username", key="su1")
    phone = st.text_input("Phone", key="su2")
    new_pass = st.text_input("Password", type="password", key="su3")
    question = st.selectbox(
    "Security Question",
    SECURITY_QUESTIONS,
    key="su4"
)
    answer = st.text_input("Security Answer", key="su5")

    if st.button("Sign Up"):
        try:
            create_user(new_user, phone, new_pass, question, answer)
            st.success("Account created 🎉")
        except Exception as e:
            st.error("User already exists or error occurred")

# FORGOT PASSWORD
# FORGOT PASSWORD (UPDATED)
with tab3:
    st.subheader("Forgot Password")

    # STEP 1: verify user + phone
    fp_user = st.text_input("Username", key="fp_user")
    fp_phone = st.text_input("Phone Number", key="fp_phone")

    if st.button("Verify User"):
        if verify_user_phone(fp_user, fp_phone):
            st.session_state["fp_verified"] = True
            st.session_state["fp_username"] = fp_user
            st.session_state["fp_question"] = get_security_question(fp_user)
        else:
            st.error("Username or phone number is incorrect ❌")

    # STEP 2: security question + reset
    if st.session_state.get("fp_verified"):
        st.info(st.session_state["fp_question"])

        answer = st.text_input("Security Answer", key="fp_answer")
        new_pass = st.text_input(
            "New Password",
            type="password",
            key="fp_new_pass"
        )

        if st.button("Reset Password"):
            if verify_security_answer(
                st.session_state["fp_username"],
                answer
            ):
                update_password(
                    st.session_state["fp_username"],
                    new_pass
                )
                st.success("Password updated successfully ✅")

                # تنظيف الـ session
                for k in [
                    "fp_verified",
                    "fp_username",
                    "fp_question"
                ]:
                    st.session_state.pop(k, None)
            else:
                st.error("Wrong security answer ❌")
