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
from frontend.login_page import render_login_page

from backend.config import initialize_directories

# --- DIRECTORY AND DB SETUP ---
initialize_directories()
st.set_page_config(page_title="헬스케어 5070", page_icon="🤗", layout="centered", initial_sidebar_state="expanded")

# --- THEME TOGGLE --- #
theme_js = """
<script>
    function applyTheme(theme) {
        const body = parent.document.body;
        body.classList.remove('light-theme', 'dark-theme');
        body.classList.add(theme);
    }

    const theme = '%s';
    applyTheme(theme);
</script>
""" % ('light-theme' if st.session_state.get('theme', '다크 모드') == '라이트 모드' else 'dark-theme')

st.markdown(theme_js, unsafe_allow_html=True)
conn = init_db()
set_background("https://images.unsplash.com/photo-1576091160550-2173dba999ef?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")

if is_logged_in():
    # --- SIDEBAR --- 
    with st.sidebar:
        st.title("🤗 헬스케어 5070")
        st.markdown("---")

        if 'theme' not in st.session_state:
            st.session_state.theme = "다크 모드"

        st.session_state.theme = st.radio(
            "화면 모드 선택",
            ("라이트 모드", "다크 모드"),
            index=1 if st.session_state.theme == "다크 모드" else 0
        )

        st.markdown("---")
        st.success(f"{st.session_state['email']}님, 환영합니다!")
        if st.button("로그아웃"):
            logout()
            st.rerun()

    # --- MAIN PAGE CONTENT ---
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

    if not articles.empty:
        st.markdown("""
            <div class="content-section">
                <h2>최신 건강 뉴스 📰</h2>
        """, unsafe_allow_html=True)
        for _, article in articles.iterrows():
            date_str = pd.to_datetime(article['crawled_date']).strftime('%Y.%m.%d')
            st.markdown(f'''
                <div class="content-list-item">
                    <span>{article["title"]}</span>
                    <span class="item-date">{date_str}</span>
                </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('<a href="/content_view" target="_self" class="custom-button">뉴스 더보기</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if not videos.empty:
        st.markdown("""
            <div class="content-section">
                <h2>최신 건강 영상 🎬</h2>
        """, unsafe_allow_html=True)
        for _, video in videos.iterrows():
            date_str = pd.to_datetime(video['created_date']).strftime('%Y.%m.%d')
            st.markdown(f'''
                <div class="content-list-item">
                    <span>{video["video_title"]}</span>
                    <span class="item-date">{date_str}</span>
                </div>
            ''', unsafe_allow_html=True)

        st.markdown('<a href="/video_view" target="_self" class="custom-button">영상 더보기</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="footer">© 2025 헬스케어 5070 프로젝트팀. All rights reserved.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    render_login_page()