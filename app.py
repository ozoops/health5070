from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import sys
import os
import pandas as pd

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.database import init_db, get_stored_articles, get_produced_videos
from frontend.utils import set_background
from frontend.auth import is_logged_in, logout

# --- PAGE AND DB SETUP ---
st.set_page_config(page_title="헬스케어 5070", page_icon="🤗", layout="wide")
conn = init_db()
set_background("https://images.unsplash.com/photo-1576091160550-2173dba999ef?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")

# --- SIDEBAR --- 
with st.sidebar:
    st.title("🤗 헬스케어 5070")
    st.markdown("---")
    if is_logged_in():
        st.success(f"{st.session_state['email']}님, 환영합니다!")
        if st.button("로그아웃"):
            logout()
            st.rerun()
    else:
        st.info("로그인 또는 회원가입을 해주세요.")

# --- MAIN PAGE CONTENT ---
if is_logged_in():
    # --- Logged-in user's homepage ---
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

else:
    # --- Public homepage for non-logged-in users ---
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.markdown("""
        <div class="login-header" style="text-align: center; padding: 4rem 1rem;">
            <h1>🤗 헬스케어 5070에 오신 것을 환영합니다</h1>
            <p style="font-size: 1.2rem; color: #D3D3D3;">AI 건강 비서와 함께하는 스마트한 건강 관리</p>
            <p style="margin-top: 2rem;">왼쪽 사이드바에서 <strong>로그인</strong> 또는 <strong>회원가입</strong>을 선택하여 시작하세요.</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)