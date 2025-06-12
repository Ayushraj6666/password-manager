import streamlit as st
from database import (
    setup_database,
    register_user,
    verify_login,
    save_password_to_db,
    get_saved_passwords,
)
import random
import string
import re

def generate_password(length, num_symbols, num_numbers):
    if length <= 8:
        st.error("Password length must be more than 8.")
        return None
    if num_symbols < 1:
        st.error("At least one symbol is required.")
        return None
    if num_numbers < 1:
        st.error("At least one number is required.")
        return None
    if num_symbols + num_numbers >= length:
        st.error("Sum of symbols and numbers must be less than length.")
        return None
    letters_count = length - num_symbols - num_numbers
    password_chars = []
    password_chars.extend(random.choices(string.ascii_letters, k=letters_count))
    password_chars.extend(random.choices(string.punctuation, k=num_symbols))
    password_chars.extend(random.choices(string.digits, k=num_numbers))
    random.shuffle(password_chars)
    return ''.join(password_chars)

def is_strong_password(password):
    return (
        len(password) > 8 and
        re.search(r'[0-9]', password) and
        re.search(r'[\W_]', password)  # symbols
    )

def main():
    st.set_page_config(page_title="Password Manager", layout="centered")
    setup_database()

    # Initialize session state
    for key, val in {
        "logged_in": False,
        "user_id": None,
        "username": "",
        "generated_password": "",
        "password_confirmed": False,
        "show_login": False
    }.items():
        if key not in st.session_state:
            st.session_state[key] = val

    st.title("🔐 Password Manager & Generator")

    if not st.session_state.logged_in:
        if st.session_state.show_login:
            # ---------------- LOGIN PAGE ----------------
            st.header("Login")
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login"):
                user_id = verify_login(login_username, login_password)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.username = login_username
                    st.success(f"Welcome back, {login_username}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

            if st.button("New user? Register here"):
                st.session_state.show_login = False
                st.rerun()
            return
        else:
            # ---------------- REGISTER PAGE ----------------
            st.header("Register")
            st.info("""
            Password must follow these rules:
            - More than 8 characters
            - At least 1 number
            - At least 1 symbol (e.g., ! @ # $)
            """)

            reg_username = st.text_input("Choose Username", key="reg_username")
            reg_password = st.text_input("Choose Password", type="password", key="reg_password")
            reg_password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")

            if st.button("Register"):
                if reg_password != reg_password_confirm:
                    st.error("Passwords do not match.")
                elif not is_strong_password(reg_password):
                    st.error("Password must be more than 8 characters and include at least one number and one symbol.")
                elif reg_username.strip() == "":
                    st.error("Username cannot be empty.")
                else:
                    success = register_user(reg_username.strip(), reg_password)
                    if success:
                        st.success("Registration successful! Please login.")
                        st.session_state.show_login = True
                        st.rerun()
                    else:
                        st.error("Username already exists or registration failed.")

            if st.button("Already a user? Login here"):
                st.session_state.show_login = True
                st.rerun()
            return

    # ---------------- MAIN LOGGED-IN INTERFACE ----------------
    st.write(f"Logged in as: **{st.session_state.username}**")
    if st.button("Logout"):
        for key in ["logged_in", "user_id", "username", "generated_password", "password_confirmed", "show_login"]:
            st.session_state[key] = False if isinstance(st.session_state[key], bool) else ""
        st.rerun()

    st.markdown("---")
    st.header("Generate a Strong Password")
    st.info("""
        Please follow these rules before generating a password:
        - Password length must be **more than 8 characters**
        - Minimum **1 symbol** required (e.g., !, @, #, $)
        - Minimum **1 number** required (0-9)
    """)

    with st.form("password_form"):
        length = st.number_input("Password Length:", min_value=9, max_value=128, value=12)
        num_symbols = st.number_input("Number of Symbols:", min_value=1, max_value=length - 2, value=2)
        num_numbers = st.number_input("Number of Numbers:", min_value=1, max_value=length - num_symbols - 1, value=2)
        generate_btn = st.form_submit_button("Generate")

    if generate_btn:
        password = generate_password(length, num_symbols, num_numbers)
        if password:
            st.session_state.generated_password = password
            st.session_state.password_confirmed = False

    if st.session_state.generated_password:
        st.subheader("Generated Password")
        st.code(st.session_state.generated_password)

        if not st.session_state.password_confirmed:
            confirm = st.radio("Do you want to save this password?", ["No", "Yes"], index=0)
            if confirm == "Yes":
                if st.button("Confirm Save"):
                    st.session_state.password_confirmed = True
                    st.rerun()
        else:
            note = st.text_input("Add a note or account name for this password:")
            if st.button("Save Password"):
                if note.strip() == "":
                    st.error("Please add a note or account name before saving.")
                else:
                    save_password_to_db(st.session_state.user_id, st.session_state.generated_password, note.strip())
                    st.success("Password and note saved successfully.")
                    st.session_state.generated_password = ""
                    st.session_state.password_confirmed = False
                    st.rerun()

    st.markdown("---")
    st.header("Your Saved Passwords")
    saved = get_saved_passwords(st.session_state.user_id)
    if not saved:
        st.info("No saved passwords yet.")
    else:
        for i, (note, pwd, created_at) in enumerate(saved, 1):
            with st.expander(f"{i}. {note} (Saved: {created_at.strftime('%Y-%m-%d %H:%M')})"):
                st.code(pwd)

if __name__ == "__main__":
    main()
