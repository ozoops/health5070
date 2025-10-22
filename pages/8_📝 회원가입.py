
import streamlit as st
import sys
import os
import re

# Add project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from frontend.auth import signup, is_logged_in
from frontend.utils import set_background

# Set background
set_background("https://images.unsplash.com/photo-1576091160550-2173dba999ef?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")

st.title("📝 회원가입")

# Email validation regex
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

if is_logged_in():
    st.info("이미 로그인되어 있습니다. 서비스를 이용하시려면 다른 페이지로 이동해주세요.")
    st.markdown(f"현재 로그인된 계정: **{st.session_state['email']}**")
else:
    with st.form("signup_form"):
        email = st.text_input("이메일", placeholder="user@example.com")
        password = st.text_input("비밀번호", type="password")
        password_confirm = st.text_input("비밀번호 확인", type="password")
        submitted = st.form_submit_button("회원가입")

        if submitted:
            if not all([email, password, password_confirm]):
                st.error("모든 필드를 입력해주세요.")
            elif not is_valid_email(email):
                st.error("유효한 이메일 주소를 입력해주세요.")
            elif password != password_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            elif len(password) < 8:
                st.error("비밀번호는 최소 8자 이상이어야 합니다.")
            else:
                success, message = signup(email, password)
                if success:
                    st.success(message)
                    st.markdown("[로그인 페이지로 이동하여 로그인하세요](로그인)")
                else:
                    st.error(message)
