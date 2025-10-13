
import streamlit as st
import sys
import os

# Add project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from frontend.auth import login, is_logged_in, logout
from frontend.utils import set_background

# Set background
set_background("https://images.unsplash.com/photo-1576091160550-2173dba999ef?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")

st.title("👤 로그인")

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
        submitted = st.form_submit_button("로그인")

        if submitted:
            if not email or not password:
                st.error("이메일과 비밀번호를 모두 입력해주세요.")
            else:
                if login(email, password):
                    st.rerun()
                else:
                    st.error("이메일 또는 비밀번호가 올바르지 않습니다.")

    st.markdown("--- ")
    st.write("아직 회원이 아니신가요?")
    # Use a link to the signup page. Streamlit doesn't have a direct st.switch_page in older versions
    # This will cause a full page reload but is a reliable way to navigate.
    st.markdown("[회원가입 페이지로 이동](회원가입)")
