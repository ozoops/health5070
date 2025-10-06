import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.database import init_db, add_user, get_user, verify_password, get_stored_articles, get_produced_videos
from frontend.utils import set_background

# --- PAGE AND DB SETUP ---
st.set_page_config(page_title="헬스케어 5070", page_icon="🤗", layout="wide")
conn = init_db()
set_background("https://images.unsplash.com/photo-1576091160550-2173dba999ef?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")


# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- AUTHENTICATION & LOGIN PAGE ---
def show_login_page():
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.markdown("""
        <div class="login-header">
            <h1>🤗 헬스케어 5070</h1>
            <p>AI 건강 비서와 함께하는 스마트한 건강 관리</p>
        </div>
    """, unsafe_allow_html=True)

    login_tab, signup_tab = st.tabs(["로그인", "회원가입"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("사용자 이름", key="login_user", placeholder="사용자 이름을 입력하세요")
            password = st.text_input("비밀번호", type="password", key="login_pass", placeholder="비밀번호를 입력하세요")
            submitted = st.form_submit_button("로그인")

            if submitted:
                user = get_user(conn, username)
                if user and verify_password(user['password'], password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.error("사용자 이름 또는 비밀번호가 올바르지 않습니다.")

    with signup_tab:
        with st.form("signup_form"):
            new_username = st.text_input("사용자 이름", key="signup_user", placeholder="원하는 사용자 이름을 입력하세요")
            new_password = st.text_input("비밀번호", type="password", key="signup_pass", placeholder="사용할 비밀번호를 입력하세요")
            confirm_password = st.text_input("비밀번호 확인", type="password", key="signup_pass_confirm", placeholder="비밀번호를 다시 한번 입력하세요")
            signup_submitted = st.form_submit_button("회원가입")

            if signup_submitted:
                if new_password != confirm_password:
                    st.error("비밀번호가 일치하지 않습니다.")
                elif not new_username or not new_password:
                    st.error("사용자 이름과 비밀번호를 모두 입력해야 합니다.")
                else:
                    if add_user(conn, new_username, new_password):
                        st.success("회원가입이 완료되었습니다. 로그인 탭에서 로그인해주세요.")
                    else:
                        st.error("이미 존재하는 사용자 이름입니다.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN APPLICATION PAGE ---
def show_main_app():
    with st.sidebar:
        st.success(f"{st.session_state['username']}님, 환영합니다!")
        st.page_link("app.py", label="홈", icon="🏠")
        st.page_link("pages/content_view.py", label="건강 뉴스(최신)", icon="📰")
        st.page_link("pages/video_view.py", label="건강 영상관", icon="🎬")
        st.page_link("pages/history_view.py", label="시청 기록", icon="📋")
        st.page_link("pages/chatbot.py", label="AI 상담", icon="🤖")
        st.page_link("pages/chat_history_view.py", label="AI 상담 기록", icon="📜")
        st.markdown("---")
        if st.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ""
            st.rerun()

    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Hero Section
    st.markdown("""
        <div class="hero-section">
            <h1>🤗 헬스케어 5070</h1>
            <p>AI 건강 비서와 함께, 맞춤형 건강 관리를 시작하세요.</p>
        </div>
    """, unsafe_allow_html=True)

    articles = get_stored_articles(conn, limit=5)
    videos = get_produced_videos(conn).head(5)

    # Define a consistent style for the list items
    item_style = "color: white; padding: 12px 0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.2);"
    date_style = "color: #bbb; font-size: 0.9em;"
    
    # Define a style for the custom buttons
    button_style = """
        display: block;
        padding: 0.75rem;
        background-color: #2A52BE; 
        color: white !important;
        text-align: center;
        border-radius: 0.5rem;
        text-decoration: none;
        margin-top: 1rem;
    """

    if not articles.empty or not videos.empty:
        col1, col2 = st.columns(2)

        if not articles.empty:
            with col1:
                st.markdown("""
                    <div style="background-color: rgba(0, 0, 0, 0.6); padding: 20px; border-radius: 10px;">
                        <h2 style="color: white;">최신 건강 뉴스 📰</h2>
                """, unsafe_allow_html=True)
                for _, article in articles.iterrows():
                    date_str = pd.to_datetime(article['crawled_date']).strftime('%Y.%m.%d')
                    st.markdown(f'<div style="{item_style}"><span>{article["title"]}</span><span style="{date_style}">{date_str}</span></div>', unsafe_allow_html=True)
                
                st.markdown(f'<a href="/content_view" target="_self" style="{button_style}">뉴스 더보기</a>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        if not videos.empty:
            with col2:
                st.markdown("""
                    <div style="background-color: rgba(0, 0, 0, 0.6); padding: 20px; border-radius: 10px;">
                        <h2 style="color: white;">최신 건강 영상 🎬</h2>
                """, unsafe_allow_html=True)
                for _, video in videos.iterrows():
                    date_str = pd.to_datetime(video['created_date']).strftime('%Y.%m.%d')
                    st.markdown(f'<div style="{item_style}"><span>{video["video_title"]}</span><span style="{date_style}">{date_str}</span></div>', unsafe_allow_html=True)

                st.markdown(f'<a href="/video_view" target="_self" style="{button_style}">영상 더보기</a>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="footer">© 2025 헬스케어 5070 프로젝트팀. All rights reserved.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE ROUTER ---
if not st.session_state['logged_in']:
    show_login_page()
else:
    show_main_app()