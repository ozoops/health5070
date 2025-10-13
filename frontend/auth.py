
import streamlit as st
import sys
import os

# Add project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.database import init_db, get_user, add_user, verify_password

# Initialize database connection
conn = init_db()

def signup(email, password):
    """Handles user signup."""
    if get_user(conn, email):
        return False, "이미 가입된 이메일입니다."
    
    if add_user(conn, email, password):
        return True, "회원가입이 완료되었습니다. 로그인해주세요."
    else:
        return False, "회원가입 중 오류가 발생했습니다."

def login(email, password):
    """Handles user login."""
    user = get_user(conn, email)
    if user and verify_password(password, user['password']):
        st.session_state['logged_in'] = True
        st.session_state['user_id'] = user['id']
        st.session_state['email'] = user['email']
        return True
    return False

def logout():
    """Logs the user out."""
    for key in list(st.session_state.keys()):
        if key in ['logged_in', 'user_id', 'email']:
            del st.session_state[key]

def is_logged_in():
    """Checks if the user is logged in."""
    return st.session_state.get('logged_in', False)
