import sys
import os
from typing import Optional
import pandas as pd
import streamlit as st

# Add project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.database import init_db, get_all_generated_content, get_produced_videos
from frontend.auth import is_logged_in
from frontend.utils import set_background

st.set_page_config(page_title="콘텐츠 허브", layout="wide")
set_background("https://images.unsplash.com/photo-1457369804613-52c61a468e7d?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")

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

st.subheader("🔍 콘텐츠 검색")
search_keyword = st.text_input("키워드를 입력하세요.", "").strip()
search_type = st.radio("검색 대상", ("전체", "뉴스", "영상"), horizontal=True)

generated_articles_all = get_all_generated_content(conn)
if not isinstance(generated_articles_all, pd.DataFrame):
    generated_articles_all = pd.DataFrame()

videos_all = get_produced_videos(conn)
if not isinstance(videos_all, pd.DataFrame):
    videos_all = pd.DataFrame()
else:
    videos_all = videos_all[videos_all["production_status"].isin(["completed", "uploaded"])]
    videos_all = videos_all.sort_values("created_date", ascending=False)

search_active = bool(search_keyword)
show_news_column = search_type != "영상"
show_video_column = search_type != "뉴스"

if search_active:
    keyword = search_keyword.lower()

    if search_type in ("전체", "뉴스"):
        articles_mask = generated_articles_all.apply(
            lambda row: keyword in str(row["generated_title"]).lower()
            or keyword in str(row["generated_content"]).lower(),
            axis=1,
        )
        generated_articles = generated_articles_all[articles_mask]
    else:
        generated_articles = pd.DataFrame()

    if search_type in ("전체", "영상"):
        videos_mask = videos_all.apply(
            lambda row: keyword in str(row["video_title"]).lower()
            or keyword in str(row["script"]).lower()
            or keyword in str(row["article_title"]).lower(),
            axis=1,
        )
        videos = videos_all[videos_mask]
    else:
        videos = pd.DataFrame()
else:
    generated_articles = (
        generated_articles_all if search_type != "영상" else pd.DataFrame()
    )
    videos = videos_all if search_type != "뉴스" else pd.DataFrame()


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

    if not show_news_column:
        st.info("검색 대상이 '영상'으로 설정되어 뉴스가 표시되지 않습니다.")
    elif search_active:
        if generated_articles.empty:
            st.info("검색된 뉴스가 없습니다.")
        else:
            st.success(f"'{search_keyword}' 관련 뉴스 결과: {len(generated_articles)}건")
            for _, article in generated_articles.iterrows():
                date_str = pd.to_datetime(article["generated_created_date"]).strftime("%Y.%m.%d")
                st.markdown(f"[{article['generated_title']} ({date_str})](?id={article['article_id']})")
    else:
        if generated_articles.empty:
            st.info("생성된 AI 기사가 아직 없습니다.")
        else:
            for _, article in generated_articles.head(5).iterrows():
                date_str = pd.to_datetime(article["generated_created_date"]).strftime("%Y.%m.%d")
                st.markdown(f"[{article['generated_title']} ({date_str})](?id={article['article_id']})")

            if len(generated_articles) > 5:
                with st.expander("뉴스 더보기"):
                    for _, article in generated_articles.iloc[5:].iterrows():
                        date_str = pd.to_datetime(article["generated_created_date"]).strftime("%Y.%m.%d")
                        st.markdown(f"[{article['generated_title']} ({date_str})](?id={article['article_id']})")
    st.markdown("</div>", unsafe_allow_html=True)

with col_videos:
    st.markdown(
        """
        <div class="content-section">
            <h2>최신 건강 영상 🎬</h2>
        """,
        unsafe_allow_html=True,
    )

    if not show_video_column:
        st.info("검색 대상이 '뉴스'로 설정되어 영상이 표시되지 않습니다.")
    elif search_active:
        if videos.empty:
            st.info("검색된 영상이 없습니다.")
        else:
            st.success(f"'{search_keyword}' 관련 영상 결과: {len(videos)}건")
            for _, video in videos.iterrows():
                date_str = pd.to_datetime(video["created_date"]).strftime("%Y.%m.%d")
                st.markdown(f"[{video['video_title']} ({date_str})](?id={video['article_id']})")
    else:
        if videos.empty:
            st.info("제작이 완료된 영상이 아직 없습니다.")
        else:
            for _, video in videos.head(5).iterrows():
                date_str = pd.to_datetime(video["created_date"]).strftime("%Y.%m.%d")
                st.markdown(f"[{video['video_title']} ({date_str})](?id={video['article_id']})")

            if len(videos) > 5:
                with st.expander("영상 더보기"):
                    for _, video in videos.iloc[5:].iterrows():
                        date_str = pd.to_datetime(video["created_date"]).strftime("%Y.%m.%d")
                        st.markdown(f"[{video['video_title']} ({date_str})](?id={video['article_id']})")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    '<div class="footer">© 2025 헬스케어 5070 프로젝트팀. All rights reserved.</div>',
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)