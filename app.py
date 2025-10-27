from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import sys
import os
import pandas as pd
from urllib.parse import quote

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.database import init_db, get_stored_articles, get_produced_videos
from frontend.utils import set_background, render_theme_selector
from frontend.auth import is_logged_in, logout
from frontend.login_page import render_login_page

from backend.config import initialize_directories

# --- DIRECTORY AND DB SETUP ---
initialize_directories()
st.set_page_config(page_title="헬스케어 5070", page_icon="🤗", layout="centered", initial_sidebar_state="expanded")
conn = init_db()
theme_mode = render_theme_selector()
set_background(
    "https://images.unsplash.com/photo-1576091160550-2173dba999ef?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    theme_mode=theme_mode,
)

st.markdown(
    """
    <style>
        a[data-testid="stPageLink"],
        .custom-button {
            display: inline-block;
            padding: 0.6rem 1.4rem;
            border-radius: 999px;
            background-color: var(--primary-color);
            color: #ffffff !important;
            text-decoration: none;
            font-weight: 700;
            transition: background-color 0.2s ease-in-out, transform 0.2s ease-in-out;
        }
        a[data-testid="stPageLink"]:hover,
        .custom-button:hover {
            background-color: var(--primary-color-hover);
            transform: translateY(-2px);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

CONTENT_PAGE_FILE = "pages/3_📰 콘텐츠 보기.py"
CONTENT_PAGE_ROUTE = "?page=" + quote("3_📰 콘텐츠 보기")

if is_logged_in():
    # --- SIDEBAR --- 
    with st.sidebar:
        st.title("🤗 헬스케어 5070")
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
        
        if hasattr(st, "page_link"):
            st.page_link(CONTENT_PAGE_FILE, label="뉴스 더보기")
        else:
            st.markdown(
                f'<a href="{CONTENT_PAGE_ROUTE}" target="_self" class="custom-button">뉴스 더보기</a>',
                unsafe_allow_html=True,
            )
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

        if hasattr(st, "page_link"):
            st.page_link(CONTENT_PAGE_FILE, label="영상 더보기")
        else:
            st.markdown(
                f'<a href="{CONTENT_PAGE_ROUTE}" target="_self" class="custom-button">영상 더보기</a>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="footer">© 2025 헬스케어 5070 프로젝트팀. All rights reserved.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    render_login_page()
