import mysql.connector
from mysql.connector import Error
import hashlib
import streamlit as st
from typing import Optional, List, Tuple


# ✅ Use Streamlit secrets instead of os.getenv
def create_connection():
    """Create and return a database connection."""
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

def setup_database():
    """Create database and tables if they don't exist."""
    try:
        # Connect without specifying database (for database creation)
        connection = mysql.connector.connect(
            host=st.secrets["db_host"],
            user=st.secrets["db_user"],
            password=st.secrets["db_password"],
            port=int(st.secrets["db_port"])
        )
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS password_manager_db;")
        cursor.close()
        connection.close()

        # Connect to the database for tables creation
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
        st.success("Database and tables are ready!")
    except Error as e:
        st.error(f"Error setting up database: {e}")

def hash_password(password: str) -> str:
    """Hash password using SHA256 for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_user_exists(username: str) -> bool:
    """Check if a username already exists."""
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists
    return False

def register_user(username: str, password: str) -> bool:
    """Register new user with hashed password."""
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
            st.error(f"Registration error: {e}")
            return False
    return False

def verify_login(username: str, password: str) -> Optional[int]:
    """Verify user credentials and return user_id if valid, else None."""
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

def save_password_to_db(user_id: int, password_value: str, account_note: str):
    """Save generated password and note linked to a user."""
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

def get_saved_passwords(user_id: int) -> List[Tuple[str, str, str]]:
    """Retrieve saved passwords and notes for a user ordered by creation date descending."""
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
