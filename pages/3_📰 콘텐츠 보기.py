import sys
import os
from typing import Optional
import pandas as pd
import streamlit as st

# Add project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.database import init_db, get_stored_articles, get_produced_videos
from frontend.auth import is_logged_in
from frontend.utils import set_background

st.set_page_config(page_title="콘텐츠 허브", layout="wide")
set_background("https://images.unsplash.com/photo-1579546929518-9e396f3cc809?q=80&w=2070&auto=format&fit=crop")

conn = init_db()

if not is_logged_in():
    st.warning("📰 콘텐츠 보기는 로그인 후 이용 가능합니다.")
    st.info("왼쪽 사이드바에서 로그인 또는 회원가입을 진행해주세요.")
    st.stop()

st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero-section">
        <h1>🤗 헬스케어 5070</h1>
        <p>AI 건강 비서와 함께, 맞춤형 건강 관리를 시작하세요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

articles = get_stored_articles(conn, limit=None) # Show all articles
if not isinstance(articles, pd.DataFrame):
    articles = pd.DataFrame()

videos = get_produced_videos(conn)
if not isinstance(videos, pd.DataFrame):
    videos = pd.DataFrame()
else:
    videos = videos[videos["production_status"].isin(["completed", "uploaded"])]
    videos = videos.sort_values("created_date", ascending=False).head(5)


def safe_page_link(target_path: str, label: str, sidebar_hint: Optional[str] = None) -> None:
    """Render a navigation link, falling back gracefully if page_link is unavailable."""
    if hasattr(st, "page_link"):
        st.page_link(target_path, label=label)
    else:
        hint = sidebar_hint or label
        st.markdown(
            f'<div style="text-align: right;"><em>사이드바에서 "{hint}" 페이지를 선택해주세요.</em></div>',
            unsafe_allow_html=True,
        )

col_news, col_videos = st.columns(2)

with col_news:
    st.markdown(
        """
        <div class="content-section">
            <h2>최신 건강 뉴스 📰</h2>
        """,
        unsafe_allow_html=True,
    )

    if articles.empty:
        st.info("수집된 최신 뉴스가 아직 없습니다.")
    else:
        for _, article in articles.iterrows():
            date_str = pd.to_datetime(article["crawled_date"]).strftime("%Y.%m.%d")
            st.markdown(
                f"""
                <div class="content-list-item">
                    <span>{article['title']}</span>
                    <span class="item-date">{date_str}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    safe_page_link("pages/3_📰 콘텐츠 보기.py", "뉴스 더보기", "📰 콘텐츠 보기")
    st.markdown("</div>", unsafe_allow_html=True)

with col_videos:
    st.markdown(
        """
        <div class="content-section">
            <h2>최신 건강 영상 🎬</h2>
        """,
        unsafe_allow_html=True,
    )

    if videos.empty:
        st.info("제작이 완료된 영상이 아직 없습니다.")
    else:
        for _, video in videos.iterrows():
            date_str = pd.to_datetime(video["created_date"]).strftime("%Y.%m.%d")
            st.markdown(
                f"""
                <div class="content-list-item">
                    <span>{video['video_title']}</span>
                    <span class="item-date">{date_str}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    safe_page_link("pages/4_🎬 영상 보기.py", "영상 더보기", "🎬 영상 보기")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    '<div class="footer">© 2025 헬스케어 5070 프로젝트팀. All rights reserved.</div>',
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)
