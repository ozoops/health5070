
import streamlit as st
import sys
import os
import pandas as pd

# Add project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.database import init_db, get_produced_videos, get_article_and_video, add_view_history, get_user
from frontend.utils import set_background
from frontend.auth import is_logged_in

# --- PAGE SETUP AND AUTH CHECK ---
st.set_page_config(page_title="건강 영상관", layout="wide")
set_background("https://images.unsplash.com/photo-1574267432553-4b4628081c31?q=80&w=1931&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")
conn = init_db()

if not is_logged_in():
    st.warning("🎬 건강 영상관은 로그인 후 이용 가능합니다.")
    st.info("왼쪽 사이드바에서 로그인 또는 회원가입을 해주세요.")
    st.stop()

# --- MAIN CONTENT ---
st.title("🎬 건강 영상관")
st.markdown("AI가 제작한 건강 동영상을 확인해보세요.")

# --- LOAD DATA ---
videos_df = get_produced_videos(conn)
if not videos_df.empty:
    videos_df = videos_df[videos_df['production_status'].isin(['completed', 'uploaded'])]

if videos_df.empty:
    st.info("아직 제작된 콘텐츠가 없습니다. 관리자 페이지에서 영상을 제작해주세요.")
else:
    sort_option = st.selectbox("정렬 기준", ["최신순", "조회순", "제목순"], label_visibility="collapsed")
    if sort_option == "조회순":
        videos_df = videos_df.sort_values('view_count', ascending=False)
    elif sort_option == "제목순":
        videos_df = videos_df.sort_values('video_title')

    st.markdown(f"총 **{len(videos_df)}**개의 동영상이 있습니다.")
    st.markdown("---")

    user = get_user(conn, st.session_state['email'])

    for _, video_row in videos_df.iterrows():
        article_id = video_row['article_id']
        
        with st.container():
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            
            if video_row['video_path'] and os.path.exists(video_row['video_path']):
                st.video(video_row['video_path'])
                if user:
                    add_view_history(conn, user['id'], video_row['id'], 'video')
            else:
                st.warning("비디오 파일을 찾을 수 없습니다.")

            st.markdown(f"<h3>{video_row['video_title']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p class='metadata'>게시일: {str(video_row['created_date'])[:10]} | 조회수: {video_row['view_count']}</p>", unsafe_allow_html=True)
            
            original_article, _, generated_article = get_article_and_video(conn, article_id)

            with st.expander("AI 생성 스크립트 보기"):
                st.markdown(video_row['script'])
            
            if generated_article:
                with st.expander("AI 생성 맞춤 기사 전문 보기"):
                    st.markdown(f"<h5>{generated_article['generated_title']}</h5>", unsafe_allow_html=True)
                    st.markdown(generated_article['generated_content'])

            
            st.markdown('</div>', unsafe_allow_html=True)