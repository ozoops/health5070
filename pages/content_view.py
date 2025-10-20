
import streamlit as st
import sys
import os
import pandas as pd

# Add project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.database import init_db, get_all_generated_content, add_view_history, get_user
from frontend.utils import set_background
from frontend.auth import is_logged_in

# --- PAGE SETUP AND AUTH CHECK ---
st.set_page_config(page_title="건강 뉴스(최신)", layout="wide")
set_background("https://images.unsplash.com/photo-1579546929518-9e396f3cc809?q=80&w=2070&auto=format&fit=crop")
conn = init_db()

if not is_logged_in():
    st.warning("📰 건강 뉴스는 로그인 후 이용 가능합니다.")
    st.info("왼쪽 사이드바에서 로그인 또는 회원가입을 해주세요.")
    st.stop()

# --- MAIN CONTENT ---
st.markdown("""
    <div style="background-color: rgba(0, 0, 0, 0.6); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="color: white;">📰 건강 뉴스(최신)</h1>
        <p style="color: white; font-size: 1.1em;">AI가 제작한 건강 영상과 맞춤 기사를 확인해보세요.</p>
    </div>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
content_df = get_all_generated_content(conn)
if not content_df.empty:
    content_df = content_df[content_df['production_status'] != 'uploaded']

if content_df.empty:
    st.info("아직 제작된 콘텐츠가 없습니다. 관리자 페이지에서 영상을 제작해주세요.")
else:
    sort_option = st.selectbox("정렬 기준", ["최신순", "조회순", "제목순"], label_visibility="collapsed")
    if sort_option == "조회순":
        content_df = content_df.sort_values('view_count', ascending=False)
    elif sort_option == "제목순":
        content_df = content_df.sort_values('generated_title')

    st.markdown(f"총 **{len(content_df)}**개의 콘텐츠가 있습니다.")
    st.markdown("---")

    user = get_user(conn, st.session_state['email'])

    for _, content_row in content_df.iterrows():
        with st.container():
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if pd.notna(content_row['video_path']) and os.path.exists(content_row['video_path']):
                    st.video(content_row['video_path'])
                    if user and pd.notna(content_row['video_id']):
                        add_view_history(conn, user['id'], content_row['video_id'], 'video')
                else:
                    # Show a placeholder if there is no video
                    st.markdown("<h4>영상 준비 중</h4>", unsafe_allow_html=True)

            with col2:
                st.markdown(f"<h3>{content_row['generated_title']}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p class='metadata'>게시일: {str(content_row['generated_created_date'])[:10]} | 조회수: {content_row.get('view_count', 0)}</p>", unsafe_allow_html=True)
                
                with st.expander("AI 생성 맞춤 기사 전문 보기"):
                    st.markdown(f"<h5>{content_row['generated_title']}</h5>", unsafe_allow_html=True)
                    st.markdown(content_row['generated_content'])
                    if user:
                        add_view_history(conn, user['id'], content_row['article_id'], 'article')

                if pd.notna(content_row['script']):
                    with st.expander("AI 생성 스크립트 보기"):
                        st.markdown(content_row['script'])

                if pd.notna(content_row['original_title']):
                    with st.expander("원본 기사 요약 보기"):
                        st.markdown(f"<strong>{content_row['original_title']}</strong>", unsafe_allow_html=True)
                        st.markdown(content_row['original_summary'])
                        if pd.notna(content_row['original_url']):
                            st.markdown(f"<a href='{content_row['original_url']}' target='_blank'>원본 기사 링크</a>", unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
