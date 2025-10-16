import streamlit as st
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import base64
import json
from datetime import datetime

# sys.path 설정
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.database import init_db, get_article_and_video

# 페이지 설정
st.set_page_config(
    page_title="헬스케어 5070",
    page_icon="🩺",
    layout="wide"
)

# 폰트 설정
plt.rcParams['font.family'] = ['NanumGothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# CSS 스타일
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Nanum Gothic', sans-serif;
    }
    
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .article-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 2rem;
        background: var(--secondary-background-color);
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .article-title {
        font-size: 2em;
        font-weight: 800;
        color: var(--text-color);
        line-height: 1.4;
        margin-bottom: 1rem;
    }
    
    .article-meta {
        color: var(--text-color);
        opacity: 0.7;
        font-size: 0.9em;
        margin-bottom: 1.5rem;
    }
    
    .article-body h3 {
        color: var(--primary-color);
        font-weight: 700;
        border-bottom: 2px solid var(--gray-40);
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    
    .article-body p {
        line-height: 1.8;
        margin-bottom: 1.2rem;
    }
    
    .image-container {
        text-align: center;
        margin: 2rem 0;
    }
    
    .chart-image, .thumbnail-image {
        max-width: 100%;
        height: auto;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .video-player {
        width: 100%;
        max-width: 800px;
        height: 450px;
        margin: 2rem auto;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .article-footer {
        text-align: center;
        color: var(--text-color);
        opacity: 0.6;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown("<div class='main-header'><h1>헬스케어 5070 - 건강 영상 보기</h1></div>", unsafe_allow_html=True)
    
    # URL에서 ID 파라미터 가져오기
    query_params = st.query_params
    article_id = query_params.get("id")

    if not article_id:
        st.info("URL에 기사 ID를 넣어주세요. 예시: `http://localhost:8501/?page=article&id=1`")
        return

    conn = init_db()
    article, video, _ = get_article_and_video(conn, article_id)

    if not article:
        st.error(f"ID {article_id}에 해당하는 기사를 찾을 수 없습니다.")
        return

    # 조회수 증가
    # add_view_count(conn, article_id) # This function is in database.py but not used in app.py, so I will comment it out for now.

    # 본문 내용 표시
    st.markdown(f"<div class='article-container'>", unsafe_allow_html=True)
    
    if video and video.get('video_path'):
        st.video(video['video_path'])

    st.markdown(f"<h2 class='article-title'>{article['title']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='article-meta'>작성일: {article['crawled_date'][:10]} | 출처: 동아일보</div>", unsafe_allow_html=True)

    st.markdown("<div class='article-body'>", unsafe_allow_html=True)
    
    # 기사 요약
    st.markdown("### 📝 기사 요약")
    st.write(article['summary'])
    
    # 영상 스크립트
    if video and video['script']:
        st.markdown("### 🎬 영상 스크립트")
        st.write(video['script'])
    
    # 본문 내용
    st.markdown("### 📖 기사 본문")
    st.write(article['content'])

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div class='article-footer'>")
    st.markdown("본 정보는 동아일보의 건강 기사를 기반으로 제작되었습니다. 의료 전문가의 진료를 대체할 수 없습니다.")
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__':
    # Streamlit에서 직접 실행 시
    if st.query_params.get("page") == "article":
        main()
    else:
        st.info("이 앱은 `app.py`에서 링크를 통해 접속해야 정상적으로 작동합니다.")
        st.info("`http://localhost:8501/?page=article&id=` 뒤에 기사 ID를 입력해 주세요.")
