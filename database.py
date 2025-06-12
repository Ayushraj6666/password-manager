import mysql.connector
from mysql.connector import Error
import hashlib
import streamlit as st
from typing import Optional, List, Tuple

# ✅ Create a DB connection using Streamlit secrets
def create_connection():
    """Create and return a connection to the specific database."""
    try:
        connection = mysql.connector.connect(
            host=st.secrets["db_host"],
            user=st.secrets["db_user"],
            password=st.secrets["db_password"],
            database=st.secrets["db_name"],
            port=int(st.secrets["db_port"])
        )
        return connection
    except Error as e:
        st.error(f"Database connection error: {e}")
        return None

# ✅ Initialize database and tables
def setup_database():
    """Create database (if not exists) and required tables."""
    try:
        # Connect to MySQL without selecting database
        connection = mysql.connector.connect(
            host=st.secrets["db_host"],
            user=st.secrets["db_user"],
            password=st.secrets["db_password"],
            port=int(st.secrets["db_port"])
        )
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {st.secrets['db_name']};")
        cursor.close()
        connection.close()

        # Connect to newly created database to create tables
        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS passwords (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    account_note VARCHAR(255),
                    password_value VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)
            conn.commit()
            cursor.close()
            conn.close()
        st.success("✅ Database and tables are set up!")
    except Error as e:
        st.error(f"Database setup failed: {e}")

# ✅ Password hashing
def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

# ✅ Check if username exists
def check_user_exists(username: str) -> bool:
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists
    return False

# ✅ Register a new user
def register_user(username: str, password: str) -> bool:
    if check_user_exists(username):
        return False
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            pwd_hash = hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, pwd_hash)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            st.error(f"Registration failed: {e}")
    return False

# ✅ Login check
def verify_login(username: str, password: str) -> Optional[int]:
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        pwd_hash = hash_password(password)
        cursor.execute(
            "SELECT id FROM users WHERE username = %s AND password_hash = %s",
            (username, pwd_hash)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return result[0]
    return None

# ✅ Save user password to DB
def save_password_to_db(user_id: int, password_value: str, account_note: str):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO passwords (user_id, password_value, account_note) VALUES (%s, %s, %s)",
            (user_id, password_value, account_note)
        )
        conn.commit()
        cursor.close()
        conn.close()

# ✅ Get saved passwords
def get_saved_passwords(user_id: int) -> List[Tuple[str, str, str]]:
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT account_note, password_value, created_at FROM passwords WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    return []
