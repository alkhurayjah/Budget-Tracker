import psycopg2
import streamlit as st

def get_connection():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],  # ← هنا التصحيح
        port=st.secrets["DB_PORT"],
    )
import hashlib

def hash_text(text: str):
    return hashlib.sha256(text.encode()).hexdigest()

def create_user(username, phone, password, question, answer):
    conn = get_connection()
    cur = conn.cursor()

    password_hash = hash_text(password)
    answer_hash = hash_text(answer)

    cur.execute("""
        INSERT INTO users (username, phone, password_hash, security_question, security_answer_hash)
        VALUES (%s, %s, %s, %s, %s)
    """, (username, phone, password_hash, question, answer_hash))

    conn.commit()
    cur.close()
    conn.close()

def authenticate_user(username, password):
    conn = get_connection()
    cur = conn.cursor()

    password_hash = hash_text(password)

    cur.execute("""
        SELECT id FROM users
        WHERE username = %s AND password_hash = %s
    """, (username, password_hash))

    user = cur.fetchone()
    cur.close()
    conn.close()

    return user
def get_security_question(username):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT security_question FROM users
        WHERE username = %s
    """, (username,))

    result = cur.fetchone()
    cur.close()
    conn.close()

    return result[0] if result else None


def verify_security_answer(username, answer):
    conn = get_connection()
    cur = conn.cursor()

    answer_hash = hash_text(answer)

    cur.execute("""
        SELECT id FROM users
        WHERE username = %s AND security_answer_hash = %s
    """, (username, answer_hash))

    result = cur.fetchone()
    cur.close()
    conn.close()

    return result is not None


def update_password(username, new_password):
    conn = get_connection()
    cur = conn.cursor()

    new_password_hash = hash_text(new_password)

    cur.execute("""
        UPDATE users
        SET password_hash = %s
        WHERE username = %s
    """, (new_password_hash, username))

    conn.commit()
    cur.close()
    conn.close()
# =====================
# EXPENSES
# =====================
def add_expense_db(user_id, expense_date, amount, category, description):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO expenses (user_id, expense_date, amount, category, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, expense_date, amount, category, description))

    conn.commit()
    cur.close()
    conn.close()


def load_expenses_db(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, expense_date, amount, category, description
        FROM expenses
        WHERE user_id = %s
        ORDER BY expense_date DESC
    """, (user_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows


def delete_expense_db(expense_id, user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM expenses
        WHERE id = %s AND user_id = %s
    """, (expense_id, user_id))

    conn.commit()
    cur.close()
    conn.close()