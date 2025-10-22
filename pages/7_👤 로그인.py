import streamlit as st
import sys
import os
import re

# Add project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from frontend.auth import login, is_logged_in, logout, signup
from frontend.utils import set_background

# Set background
set_background("https://images.unsplash.com/photo-1576091160550-2173dba999ef?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")

st.title("👤 로그인")

# Email validation regex
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

if is_logged_in():
    st.success(f"**{st.session_state['email']}**님, 환영합니다!")
    st.write("다른 페이지로 이동하여 서비스를 이용할 수 있습니다.")
    if st.button("로그아웃"):
        logout()
        st.rerun()
else:
    with st.form("login_form"):
        email = st.text_input("이메일", placeholder="user@example.com")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인", type="primary")

        if submitted:
            if not email or not password:
                st.error("이메일과 비밀번호를 모두 입력해주세요.")
            else:
                if login(email, password):
                    st.rerun()
                else:
                    st.error("이메일 또는 비밀번호가 올바르지 않습니다.")

    st.markdown("---")
    with st.expander("아직 회원이 아니신가요? 회원가입"):
        with st.form("signup_form_in_login"):
            st.subheader("회원가입")
            
            email_signup = st.text_input("이메일", placeholder="user@example.com", key="signup_email")
            password_signup = st.text_input("비밀번호", type="password", key="signup_password")
            password_confirm = st.text_input("비밀번호 확인", type="password", key="signup_password_confirm")
            
            signup_submitted = st.form_submit_button("회원가입")

            if signup_submitted:
                if not all([email_signup, password_signup, password_confirm]):
                    st.error("모든 필드를 입력해주세요.")
                elif not is_valid_email(email_signup):
                    st.error("유효한 이메일 주소를 입력해주세요.")
                elif password_signup != password_confirm:
                    st.error("비밀번호가 일치하지 않습니다.")
                elif len(password_signup) < 8:
                    st.error("비밀번호는 최소 8자 이상이어야 합니다.")
                else:
                    success, message = signup(email_signup, password_signup)
                    if success:
                        st.success(message)
                        st.info("이제 위 로그인 양식에서 로그인할 수 있습니다.")
                    else:
                        st.error(message)