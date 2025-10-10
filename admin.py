# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import time
from datetime import datetime
import sqlite3
import re
import requests
from bs4 import BeautifulSoup
import base64
from pathlib import Path
import json

# --- 백엔드 모듈 import를 위한 경로 설정 ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import init_db, get_produced_videos, get_crawl_stats, get_stored_articles, get_generated_article, save_generated_article
from backend.crawler import DongACrawler
from backend.video import VideoProducer, display_video_card
from backend.article_generator import ArticleGenerator

# --- 페이지 설정 및 CSS 스타일링 ---
st.set_page_config(
    page_title="헬스케어 5070 - 영상 제작 시스템",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)
# 💡 폰트 경로 오류를 방지하기 위해 폰트 설정 전에 확인합니다.
try:
    plt.rcParams['font.family'] = ['NanumGothic', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except Exception:
    pass

st.markdown(
    '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Nanum Gothic', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        text-align: center;
    }
    
    .video-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #667eea;
    }
    
    .video-title {
        font-size: 1.3em;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    .video-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #666;
        font-size: 0.9em;
        margin-bottom: 1rem;
    }
    
    .production-status {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: 600;
    }
    
    .status-processing {
        background: #fff3cd;
        color: #856404;
    }
    
    .status-completed {
        background: #d4edda;
        color: #155724;
    }
    
    .status-error {
        background: #f8d7da;
        color: #721c24;
    }
    
    .script-preview {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        font-size: 0.9em;
        line-height: 1.6;
        max-height: 200px;
        overflow-y: auto;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .stat-number {
        font-size: 2em;
        font-weight: 800;
        color: #667eea;
    }
    
    .stat-label {
        color: #666;
        font-size: 0.9em;
        margin-top: 0.5rem;
    }
    
    .article-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }
    
    .article-card:hover {
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    .article-title {
        font-size: 1.2em;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }
    
    .article-summary {
        color: #666;
        font-size: 0.95em;
        line-height: 1.5;
        margin-bottom: 0.8rem;
    }
    
    .article-meta {
        font-size: 0.85em;
        color: #888;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .article-link {
        color: #00796b;
        text-decoration: none;
        font-weight: 600;
    }
    
    .health-tag {
        background: #00a085;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8em;
        margin-right: 0.5rem;
    }

    @media (max-width: 768px) {
        /* Streamlit 컬럼을 세로로 쌓기 */
        div[data-testid="column"] {
            flex: 1 1 100% !important;
            max-width: 100% !important;
            padding: 0 !important;
        }
        
        .main-header h1 {
            font-size: 1.8rem;
        }
        
        .main-header p {
            font-size: 1rem;
        }

        .article-title {
            font-size: 1.1em;
        }

        /* 버튼들을 화면 너비에 맞게 조정 */
        .stButton>button {
            width: 100% !important;
            margin-top: 10px;
        }
        
        .stats-grid {
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        }
    }
</style>
''', unsafe_allow_html=True)

if 'video_to_produce' not in st.session_state:
    st.session_state.video_to_produce = None

def main():
    st.markdown(
        '''
    <div class="main-header">
        <h1>헬스케어 5070 - 영상 제작 시스템</h1>
        <p>크롤링된 건강정보를 자동으로 영상 콘텐츠로 제작합니다</p>
    </div>
    ''', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs([" 기사 수집 및 영상 제작", " 영상 관리", " 통계", " 동영상 업로드"])
    
    with tab1:
        if st.session_state.get('video_to_produce'):
            article = st.session_state.video_to_produce
            st.markdown(f"#### 영상 제작: {article['title']}")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(" 영상 제작 시작", type="primary"):
                    producer = VideoProducer()
                    article_generator = ArticleGenerator()
                    conn = init_db()
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    try:
                        # ------------------------------------------------
                        # 💡 [수정 사항]: 입력 텍스트 길이 제한 (토큰 초과 방지)
                        # ------------------------------------------------
                        MAX_CHARS_FOR_AI = 300000 
                        original_content = article['content']
                        
                        if len(original_content) > MAX_CHARS_FOR_AI:
                            trimmed_content = original_content[:MAX_CHARS_FOR_AI]
                            st.warning("⚠️ **입력 텍스트가 너무 길어 AI 모델 한도를 초과할 수 있어, 앞부분 30만 글자만 사용하여 요약합니다.**")
                        else:
                            trimmed_content = original_content
                        
                        status_text.text(" 스크립트 요약 중...")
                        # 수정된 (제한된) 내용을 전달
                        short_script = article_generator.generate_short_script(trimmed_content)
                        # ------------------------------------------------
                        # (이하 동일)
                        st.info(f"생성된 스크립트: {short_script}") # for debugging
                        progress_bar.progress(25)
                        
                        status_text.text(" 썸네일 생성 중...")
                        video_data = producer.produce_video_content(article, short_script)
                        progress_bar.progress(100)

                        video_id = producer.save_video_data(video_data, conn)
                        status_text.text(" 영상 제작 완료!")
                        st.success(f"영상이 성공적으로 제작되었습니다! (ID: {video_id})")
                        st.markdown("###  제작 완료!")
                        
                        st.session_state.video_to_produce = None
                        st.rerun()

                    except Exception as e:
                        st.error(f"영상 제작 중 오류가 발생했습니다: {str(e)}")
            with col2:
                if st.button("취소"):
                    st.session_state.video_to_produce = None
                    st.rerun()

        else:
            st.markdown("###  헬스동아 기사 크롤링")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(" 기사 크롤링 시작", type="primary"):
                    crawler = DongACrawler()
                    with st.spinner("헬스동아에서 기사를 수집하고 있습니다..."):
                        articles = crawler.crawl_health_articles()
                        conn = init_db()
                        if articles:
                            new_count, age_relevant = crawler.save_articles(articles, conn)
                            st.success(f" 새 기사 {new_count}개 수집 (관련 기사: {age_relevant}개)")
                        else:
                            st.warning("새로운 기사를 찾지 못했습니다.")
            with col2:
                show_all = st.checkbox("전체 기사 보기", value=False)
            
            st.markdown("---")
            
            articles_df = pd.DataFrame()
            if os.path.exists('health_dongA.db'):
                articles_df = get_stored_articles(
                    conn=init_db(),
                    age_relevant_only=not show_all, 
                    limit=20
                )
            
            if not articles_df.empty:
                st.markdown(f"###  {'전체' if show_all else '50-70세 관련'} 건강 기사 ({len(articles_df)}개)")
                for _, article_row in articles_df.iterrows():
                    article = article_row.to_dict()
                    conn = init_db()
                    has_video = not pd.read_sql_query("SELECT id FROM videos WHERE article_id = ?", conn, params=[article['id']]).empty
                    generated_article = get_generated_article(conn, article['id'])

                    video_icon = "" if has_video else ""
                    ai_icon = "" if generated_article else ""
                    tags_html = ' '.join([f'<span class="health-tag">{kw}</span>' for kw in article['keywords'].split(', ')[:3]]) if article['keywords'] else ""
                    relevance_icon = "" if article['is_age_relevant'] else ""
                    
                    with st.container(border=True):
                        st.markdown(f"<div class='article-title'>{video_icon} {ai_icon} {relevance_icon} {article['title']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='article-summary'>{article['summary']}</div>", unsafe_allow_html=True)
                        
                        meta_col1, meta_col2 = st.columns([3, 1])
                        with meta_col1:
                            st.markdown(f"{tags_html} <span style='color: #aaa;'>Crawled: {article['crawled_date'][:10]}</span>", unsafe_allow_html=True)
                        with meta_col2:
                            st.markdown(f"<a href='{article['url']}' target='_blank' class='article-link'>Read Original →</a>", unsafe_allow_html=True)

                        # --- Button Section ---
                        if article['is_age_relevant']:
                            st.markdown("---")
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                if st.button(" AI 기사 생성", key=f"make_ai_article_{article['id']}", disabled=bool(generated_article)):
                                    with st.spinner("AI가 관련 자료를 분석하고 기사를 생성하고 있습니다..."):
                                        try:
                                            article_generator = ArticleGenerator()
                                            # Combine title and content for the agent prompt
                                            prompt = f"기사 제목: {article['title']}\n\n기사 내용: {article['content']}\n\n위 제목과 내용을 바탕으로 50대-70대 독자를 위해 더 이해하기 쉽고 유용한 새로운 건강 기사를 작성해줘."
                                            generated_content = article_generator.run_agent(prompt)
                                            
                                            # For now, we'll use the original title and handle the content
                                            # In a real scenario, you might want to parse the title from the generated content
                                            generated_title = article['title'] + " (AI 생성)"

                                            if generated_title and generated_content:
                                                new_article_data = {
                                                    'article_id': article['id'],
                                                    'generated_title': generated_title,
                                                    'generated_content': generated_content
                                                }
                                                save_generated_article(conn, new_article_data)
                                                st.success("AI 기사가 성공적으로 생성되었습니다!")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("AI 기사 생성에 실패했습니다. API 키 또는 네트워크 연결을 확인하세요.")
                                        except Exception as e:
                                            st.error(f"AI 기사 생성 중 오류가 발생했습니다: {e}")
                                            st.error(f"오류 유형: {type(e)}")
                                            import traceback
                                            st.text(traceback.format_exc())

                            with btn_col2:
                                if not has_video:
                                    if st.button(" AI 영상 제작", key=f"ai_video_{article['id']}", disabled=not generated_article):
                                        st.session_state.video_to_produce = {
                                            'id': article['id'],
                                            'title': generated_article['generated_title'],
                                            'content': generated_article['generated_content'],
                                            'crawled_date': generated_article['created_date']
                                        }
                                        st.rerun()

                            if generated_article:
                                with st.expander(" AI 생성 기사 보기", expanded=False):
                                    st.header(generated_article['generated_title'])
                                    st.markdown(generated_article['generated_content'])
                                    created_date_str = generated_article['created_date'][:10]
                                    footer_text = f"기사작성일 : {created_date_str}, (c) 2025 헬스케어 5070. All rights reserved"
                                    st.markdown(f"<div style=\"text-align: left; font-size: small; color: grey; margin-top: 20px;\">{footer_text}</div>", unsafe_allow_html=True)

            else:
                st.info(" 크롤링된 기사가 없습니다. 위의 '크롤링 시작' 버튼을 눌러주세요!")

    with tab2:
        st.markdown("###  제작된 영상 관리")
        videos_df = get_produced_videos(conn=init_db())
        if not videos_df.empty:
            sort_option = st.selectbox("정렬 기준", ["최신순", "조회순", "제목순"])
            show_count = st.selectbox("표시 개수", [5, 10, 20], index=1)
            if sort_option == "조회순":
                videos_df = videos_df.sort_values('view_count', ascending=False)
            elif sort_option == "제목순":
                videos_df = videos_df.sort_values('video_title')
            for _, video in videos_df.head(show_count).iterrows():
                display_video_card(video.to_dict())
                
                # '기사/영상 보기' 버튼 추가
                st.markdown(f'[<button style="background-color: #00a085; color: white; border: none; padding: 10px 20px; border-radius: 25px; cursor: pointer; font-family: \'Nanum Gothic\', sans-serif;"> 기사/영상 보기</button>](http://localhost:8501/app_article?id={video["article_id"]})', unsafe_allow_html=True)
                
                st.markdown("---")
        else:
            st.info("제작된 영상이 없습니다. 먼저 기사를 크롤링하고 영상을 제작해보세요.")

    with tab3:
        st.markdown("###  제작 통계 및 분석")
        conn = init_db()
        stats_query = '''
        SELECT COUNT(*) as total_articles, COUNT(CASE WHEN is_age_relevant = 1 THEN 1 END) as relevant_articles,
               (SELECT COUNT(*) FROM videos) as total_videos,
               (SELECT SUM(view_count) FROM videos) as total_views
        FROM articles
        '''
        stats_df = pd.read_sql_query(stats_query, conn)
        if not stats_df.empty:
            stats = stats_df.iloc[0]
            st.markdown(f'''
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{int(stats['total_articles']) if stats['total_articles'] else 0}</div>
                    <div class="stat-label">총 수집 기사</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{int(stats['relevant_articles']) if stats['relevant_articles'] else 0}</div>
                    <div class="stat-label">관련 기사</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{int(stats['total_videos']) if stats['total_videos'] else 0}</div>
                    <div class="stat-label">제작된 영상</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{int(stats['total_views']) if stats['total_views'] else 0}</div>
                    <div class="stat-label">총 조회수</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("####  기사 수집 현황")
                daily_stats = pd.read_sql_query('''
                    SELECT DATE(crawled_date) as date, COUNT(*) as count, COUNT(CASE WHEN is_age_relevant = 1 THEN 1 END) as relevant_count
                    FROM articles WHERE crawled_date > datetime('now', '-7 days') GROUP BY DATE(crawled_date) ORDER BY date
                ''', conn)
                if not daily_stats.empty:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.plot(daily_stats['date'], daily_stats['count'], 'o-', label='전체 기사', color='#667eea')
                    ax.plot(daily_stats['date'], daily_stats['relevant_count'], 's-', label='관련 기사', color='#764ba2')
                    ax.set_title('최근 7일 기사 수집 현황')
                    ax.set_ylabel('기사 수')
                    ax.legend()
                    ax.tick_params(axis='x', rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                else: st.info("표시할 수집 데이터가 없습니다.")
            with col2:
                st.markdown("####   영상 제작 현황")
                video_stats = pd.read_sql_query("SELECT production_status, COUNT(*) as count FROM videos GROUP BY production_status", conn)
                if not video_stats.empty:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    colors = {'completed': '#4CAF50', 'processing': '#FF9800', 'error': '#F44336', 'uploaded': '#2196F3'}
                    status_colors = [colors.get(status, '#9E9E9E') for status in video_stats['production_status']]
                    bars = ax.bar(video_stats['production_status'], video_stats['count'], color=status_colors)
                    ax.set_title('영상 제작 상태 분포')
                    ax.set_ylabel('영상 수')
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height, f'{int(height)}', ha='center', va='bottom')
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                else: st.info("제작된 영상이 없습니다.")
            st.markdown("####  키워드 분석")
            keyword_stats = pd.read_sql_query("SELECT keywords FROM articles WHERE keywords != '' AND is_age_relevant = 1", conn)
            if not keyword_stats.empty:
                all_keywords = []
                for keywords_str in keyword_stats['keywords']:
                    if keywords_str:
                        keywords_list = [kw.strip() for kw in keywords_str.split(',')]
                        all_keywords.extend(keywords_list)
                if all_keywords:
                    keyword_counts = pd.Series(all_keywords).value_counts().head(10)
                    fig, ax = plt.subplots(figsize=(10, 6))
                    bars = ax.barh(keyword_counts.index[::-1], keyword_counts.values[::-1], color='#667eea')
                    ax.set_title('상위 10개 건강 키워드')
                    ax.set_xlabel('출현 빈도')
                    for i, bar in enumerate(bars):
                        width = bar.get_width()
                        ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, f'{int(width)}', ha='left', va='center')
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                else: st.info("키워드 데이터가 충분하지 않습니다.")
            else: st.info("분석할 키워드가 없습니다.")
        else: st.info("표시할 통계 데이터가 없습니다.")

    with tab4:
        st.markdown("###  동영상 직접 업로드")

        with st.form(key="upload_form"):
            uploaded_file = st.file_uploader("업로드할 동영상 파일을 선택하세요.", type=["mp4", "mov", "avi"])
            video_title = st.text_input("동영상 제목")
            video_script = st.text_area("동영상 설명 (스크립트)")
            submitted = st.form_submit_button("업로드 시작")

        if submitted:
            if uploaded_file is not None and video_title:
                # 1. Create upload directory if it doesn't exist
                upload_dir = "uploaded_videos"
                os.makedirs(upload_dir, exist_ok=True)

                # 2. Save the file
                file_path = os.path.join(upload_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                conn = init_db()
                c = conn.cursor()

                try:
                    # 3. Create a dummy article
                    c.execute('''
                        INSERT INTO articles (title, summary, content, is_age_relevant, crawled_date, url)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (video_title, video_script[:100], video_script, True, datetime.now(), f"#{video_title.replace(' ', '')}"))
                    article_id = c.lastrowid

                    # 4. Create a video record
                    c.execute('''
                        INSERT INTO videos (article_id, video_title, script, video_path, production_status, created_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (article_id, video_title, video_script, file_path, 'uploaded', datetime.now()))

                    conn.commit()
                    st.success(f"'{video_title}' 동영상을 성공적으로 업로드했습니다.")
                except sqlite3.IntegrityError:
                    st.error("이미 같은 제목의 동영상이 존재하거나, URL이 중복됩니다. 제목을 변경해주세요.")
                except Exception as e:
                    st.error(f"업로드 중 오류가 발생했습니다: {e}")
                finally:
                    conn.close()

            else:
                st.warning("동영상 파일과 제목을 모두 입력해주세요.")

    with st.sidebar:
        st.markdown("###   영상 제작 시스템")
        st.markdown("**기능:**")
        st.markdown("-  헬스동아 크롤링")
        st.markdown("-  자동 스크립트 생성")
        st.markdown("-  썸네일 생성")
        st.markdown("-  건강 차트 생성")
        st.markdown("-   영상 콘텐츠 조합")
        st.markdown("---")
        st.markdown("###  제작 설정")
        video_length = st.slider("영상 길이 (초)", 30, 300, 120)
        include_charts = st.checkbox("차트 포함", True)
        include_thumbnails = st.checkbox("썸네일 생성", True)
        auto_production = st.checkbox("자동 제작 모드", False)
        st.markdown("---")
        st.markdown("###  빠른 통계")
        conn = init_db()
        quick_stats = pd.read_sql_query('''
            SELECT (SELECT COUNT(*) FROM articles WHERE is_age_relevant = 1) as articles,
                   (SELECT COUNT(*) FROM videos WHERE production_status = 'completed') as videos,
                   (SELECT COUNT(*) FROM articles a LEFT JOIN videos v ON a.id = v.article_id WHERE v.id IS NULL AND a.is_age_relevant = 1) as pending
        ''', conn)
        if not quick_stats.empty:
            stats = quick_stats.iloc[0]
            st.metric("관련 기사", int(stats['articles']) if stats['articles'] else 0)
            st.metric("완성 영상", int(stats['videos']) if stats['videos'] else 0)
            st.metric("제작 대기", int(stats['pending']) if stats['pending'] else 0)

    st.markdown("---")
    footer_html = """
    <div style="text-align: center; color: #777; padding: 2rem;">
        <h4> 헬스케어 5070 - 영상 제작 시스템</h4>
        <p>크롤링된 건강정보를 자동으로 영상 콘텐츠로 제작합니다</p>
        <p> 제작된 영상은 교육 및 정보 제공 목적이며, 전문의 진료를 대체할 수 없습니다. </p>
        <p>(c) 2025 헬스케어 5070 영상 제작 시스템</p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()