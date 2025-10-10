import streamlit as st
import sys
import os
import pandas as pd

# Add project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.database import init_db, get_produced_videos, get_article_and_video, add_view_history, get_user
from frontend.utils import set_background

# --- PAGE SETUP AND AUTH CHECK ---
st.set_page_config(page_title="건강 뉴스(최신)", layout="wide")
set_background("https://images.unsplash.com/photo-1579546929518-9e396f3cc809?q=80&w=2070&auto=format&fit=crop")
conn = init_db()

if not st.session_state.get('logged_in'):
    st.error("이 페이지에 접근하려면 로그인이 필요합니다.")
    st.stop()

# --- SIDEBAR ---
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

# --- MAIN CONTENT ---
st.markdown("""
    <div style="background-color: rgba(0, 0, 0, 0.6); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="color: white;">📰 건강 뉴스(최신)</h1>
        <p style="color: white; font-size: 1.1em;">AI가 제작한 건강 영상과 맞춤 기사를 확인해보세요.</p>
    </div>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
videos_df = get_produced_videos(conn)
if not videos_df.empty:
    videos_df = videos_df[videos_df['production_status'] != 'uploaded']

if videos_df.empty:
    st.info("아직 제작된 콘텐츠가 없습니다. 관리자 페이지에서 영상을 제작해주세요.")
else:
    sort_option = st.selectbox("정렬 기준", ["최신순", "조회순", "제목순"], label_visibility="collapsed")
    if sort_option == "조회순":
        videos_df = videos_df.sort_values('view_count', ascending=False)
    elif sort_option == "제목순":
        videos_df = videos_df.sort_values('video_title')

    st.markdown(f"총 **{len(videos_df)}**개의 콘텐츠가 있습니다.")
    st.markdown("---")

    for _, video_row in videos_df.iterrows():
        article_id = video_row['article_id']
        
        with st.container():
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if video_row['video_path'] and os.path.exists(video_row['video_path']):
                    st.video(video_row['video_path'])
                    if 'username' in st.session_state and st.session_state['username']:
                        user = get_user(conn, st.session_state['username'])
                        if user:
                            add_view_history(conn, user['id'], video_row['id'], 'video')
                else:
                    st.warning("비디오 파일을 찾을 수 없습니다.")

            with col2:
                st.markdown(f"<h3>{video_row['video_title']}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p class='metadata'>게시일: {str(video_row['created_date'])[:10]} | 조회수: {video_row['view_count']}</p>", unsafe_allow_html=True)
                
                original_article, _, generated_article = get_article_and_video(conn, article_id)

                with st.expander("AI 생성 스크립트 보기"):
                    st.markdown(video_row['script'])
                
                if generated_article:
                    with st.expander("AI 생성 맞춤 기사 전문 보기"):
                        st.markdown(f"<h5>{generated_article['generated_title']}</h5>", unsafe_allow_html=True)
                        st.markdown(generated_article['generated_content'])
                        if 'username' in st.session_state and st.session_state['username']:
                            user = get_user(conn, st.session_state['username'])
                            if user:
                                add_view_history(conn, user['id'], article_id, 'article')

                if original_article:
                    with st.expander("원본 기사 요약 보기"):
                        st.markdown(f"<strong>{original_article['title']}</strong>", unsafe_allow_html=True)
                        st.markdown(original_article['summary'])
                        st.markdown(f"<a href='{original_article['url']}' target='_blank'>원본 기사 링크</a>", unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
