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

# --- 백엔드 모듈 import를 위한 경로 설정 ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import init_db, get_produced_videos, get_crawl_stats, get_stored_articles, get_generated_article, save_generated_article, delete_video
from backend.crawler import DongACrawler
from backend.video import VideoProducer, display_video_card
from backend.article_generator import ArticleGenerator
from backend.config import UPLOAD_DIR, data_dir


def _configure_admin_environment() -> None:
    """관리자 화면을 위한 폰트 및 공통 CSS를 적용합니다."""
    if st.session_state.get('_admin_env_configured'):
        return
    try:
        font_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'fonts',
            'NanumGothic-Regular.ttf'
        )
        font_prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
    except FileNotFoundError:
        st.warning("나눔고딕 폰트를 찾을 수 없습니다. 'fonts/NanumGothic-Regular.ttf' 경로에 폰트를 추가해 주세요. 일부 텍스트가 깨질 수 있습니다.")
        plt.rcParams['font.family'] = ['DejaVu Sans']  # Fallback font

    plt.rcParams['axes.unicode_minus'] = False

    st.markdown(
        '''
<style>
    /* CSS is inherited from the main app, but we can add specific styles if needed */
    .main-header {
        background: var(--primary-color);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        text-align: center;
    }
    .stats-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        justify-content: space-around;
    }
    .stat-card {
        background-color: var(--secondary-background-color);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        flex-grow: 1;
        min-width: 200px;
        border: 1px solid var(--gray-20);
    }
    .stat-number {
        font-size: 3em;
        font-weight: 800;
        color: var(--primary-color);
    }
    .stat-label {
        font-size: 1.2em;
        color: var(--text-color);
        opacity: 0.8;
    }
</style>
''',
        unsafe_allow_html=True
    )
    st.session_state['_admin_env_configured'] = True


def _ensure_admin_state() -> None:
    if 'video_to_produce' not in st.session_state:
        st.session_state.video_to_produce = None


def show_admin_page():
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
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    try:
                        MAX_CHARS_FOR_AI = 300000 
                        original_content = article['content']
                        
                        if len(original_content) > MAX_CHARS_FOR_AI:
                            trimmed_content = original_content[:MAX_CHARS_FOR_AI]
                            st.warning("⚠️ **입력 텍스트가 너무 길어 AI 모델 한도를 초과할 수 있어, 앞부분 30만 글자만 사용하여 요약합니다.**")
                        else:
                            trimmed_content = original_content
                        
                        status_text.text(" 스크립트 요약 중...")
                        short_script = article_generator.generate_short_script(trimmed_content)
                        st.info(f"생성된 스크립트: {short_script}")
                        progress_bar.progress(25)
                        
                        status_text.text(" 썸네일 생성 중...")
                        video_data = producer.produce_video_content(article, short_script)
                        progress_bar.progress(100)

                        conn = init_db() # Get a fresh connection right before the DB write
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

                    tags_html = ' '.join([f'<span class="health-tag">{kw}</span>' for kw in article['keywords'].split(', ')[:3]]) if article['keywords'] else ""
                    
                    with st.container(border=True):
                        st.markdown(f"<div class='article-title'>{article['title']}</div>", unsafe_allow_html=True)
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
                                            
                                            full_generated_article = article_generator.generate_new_article(
                                                title=article['title'],
                                                content=article['content']
                                            ).strip()

                                            if full_generated_article:
                                                # Fallback logic for title and content
                                                if '\n' in full_generated_article:
                                                    parts = full_generated_article.split('\n', 1)
                                                    generated_title = parts[0].strip()
                                                    generated_content = parts[1].strip()
                                                else:
                                                    st.warning("AI가 생성한 제목이 없어 원본 제목을 사용합니다.")
                                                    generated_title = article['title']
                                                    generated_content = full_generated_article

                                                # Check for known failure messages
                                                if "죄송합니다" in full_generated_article:
                                                    st.error(f"AI 기사 생성에 실패했습니다: {full_generated_article}")
                                                else:
                                                    new_article_data = {
                                                        'article_id': article['id'],
                                                        'generated_title': generated_title,
                                                        'generated_content': generated_content
                                                    }
                                                    conn = init_db()
                                                    save_generated_article(conn, new_article_data)
                                                    st.success("AI 기사가 성공적으로 생성되었습니다!")
                                                    time.sleep(1)
                                                    st.rerun()
                                            else:
                                                st.error("AI 기사 생성에 실패했습니다. AI 모델로부터 아무런 내용을 받지 못했습니다.")

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
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    # '기사/영상 보기' 버튼 추가
                    st.markdown(f'[<button style="background-color: #00a085; color: white; border: none; padding: 10px 20px; border-radius: 25px; cursor: pointer; font-family: \'Nanum Gothic\', sans-serif;"> 기사/영상 보기</button>](http://localhost:8501/app_article?id={video["article_id"]})', unsafe_allow_html=True)
                with col2:
                    if st.button("삭제", key=f"delete_video_{video['id']}", type="primary"):
                        conn = init_db()
                        video_path_from_db = delete_video(conn, video['id'])
                        
                        if video_path_from_db:
                            # video_path_from_db가 절대 경로가 아닐 수 있으므로, data_dir를 기준으로 절대 경로를 구성합니다.
                            if not os.path.isabs(video_path_from_db):
                                video_path = os.path.join(data_dir, video_path_from_db)
                            else:
                                video_path = video_path_from_db

                            if os.path.isfile(video_path):
                                try:
                                    os.remove(video_path)
                                    st.success(f"'{video['video_title']}' 영상이 성공적으로 삭제되었습니다.")
                                    time.sleep(1)
                                    st.rerun()
                                except OSError as e:
                                    st.error(f"영상 파일 삭제 중 오류가 발생했습니다: {e}")
                            else:
                                st.warning("영상을 DB에서 삭제했지만, 실제 파일을 찾지 못했습니다.")
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.warning("삭제할 영상 정보를 DB에서 찾지 못했습니다.")
                            time.sleep(1)
                            st.rerun()

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
            total_articles = int(stats['total_articles']) if stats['total_articles'] else 0
            relevant_articles = int(stats['relevant_articles']) if stats['relevant_articles'] else 0
            total_videos = int(stats['total_videos']) if stats['total_videos'] else 0
            total_views = int(stats['total_views']) if stats['total_views'] else 0

            st.markdown("#### 제작 통계 및 분석")
            metric_cols = st.columns(4)
            metrics = [
                ("총 수집 기사", f"{total_articles:,}"),
                ("관련 기사", f"{relevant_articles:,}"),
                ("제작된 영상", f"{total_videos:,}"),
                ("총 조회수", f"{total_views:,}"),
            ]

            for col, (label, value) in zip(metric_cols, metrics):
                with col:
                    st.metric(label, value)

            st.markdown("")
            st.markdown("#### 기사 수집 현황")
            daily_stats = pd.read_sql_query('''
                SELECT DATE(crawled_date) as date, COUNT(*) as count, COUNT(CASE WHEN is_age_relevant = 1 THEN 1 END) as relevant_count
                FROM articles WHERE crawled_date > datetime('now', '-7 days') GROUP BY DATE(crawled_date) ORDER BY date
            ''', conn)
            if not daily_stats.empty:
                fig, ax = plt.subplots(figsize=(10, 4))
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

            st.markdown("<hr>", unsafe_allow_html=True)

            st.markdown("#### 영상 제작 현황")
            video_stats = pd.read_sql_query("SELECT production_status, COUNT(*) as count FROM videos GROUP BY production_status", conn)
            if not video_stats.empty:
                fig, ax = plt.subplots(figsize=(10, 4))
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

            st.markdown("<hr>", unsafe_allow_html=True)

            st.markdown("#### 키워드 분석")
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
                file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                conn = init_db()
                c = conn.cursor()

                try:
                    c.execute('''
                        INSERT INTO articles (title, summary, content, is_age_relevant, crawled_date, url)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (video_title, video_script[:100], video_script, False, datetime.now(), f"#{video_title.replace(' ', '')}"))
                    article_id = c.lastrowid

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


ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin0326')


def render_admin_portal() -> None:
    _configure_admin_environment()
    _ensure_admin_state()

    password = st.text_input('관리자 비밀번호를 입력하세요', type='password')

    if password == ADMIN_PASSWORD:
        show_admin_page()
    elif password:
        st.error('비밀번호가 올바르지 않습니다.')
    else:
        st.info('관리자 기능을 이용하려면 비밀번호를 입력해 주세요.')


if __name__ == '__main__':
    render_admin_portal()
