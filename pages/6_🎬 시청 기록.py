
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(os.path.join(__file__, '..', '..'))))
from backend.database import get_view_history, init_db, get_user, toggle_favorite, delete_history_item, delete_all_history
from frontend.utils import set_background
from frontend.auth import is_logged_in

st.set_page_config(page_title="시청 기록", layout="wide")
set_background("https://images.unsplash.com/photo-1489599849927-2ee91e4543e3?q=80&w=2073&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")

st.title("🎬 시청 기록")

if not is_logged_in():
    st.warning("📋 시청 기록은 로그인 후 이용 가능합니다.")
    st.info("왼쪽 사이드바에서 로그인 또는 회원가입을 해주세요.")
    st.stop()

conn = init_db()
user = get_user(conn, st.session_state['email'])

if user:
    user_id = user['id']
    history_df = get_view_history(conn, user_id)

    # --- Filters and Search ---
    col1, col2, col3 = st.columns(3)
    with col1:
        search_query = st.text_input("🔍 제목으로 검색", key="search_history")
    with col2:
        date_filter = st.selectbox("📅 날짜 필터", ["전체", "오늘", "이번 주", "이번 달"], key="date_filter_history")
    with col3:
        category_filter = st.selectbox("🏷️ 카테고리 필터", ["전체", "뉴스만", "영상만"], key="category_filter_history")

    if not history_df.empty:
        history_df['viewed_at'] = pd.to_datetime(history_df['viewed_at'])

        # Apply filters
        if search_query:
            history_df = history_df[history_df['title'].str.contains(search_query, case=False, na=False)]
        
        today = datetime.now().date()
        if date_filter == "오늘":
            history_df = history_df[history_df['viewed_at'].dt.date == today]
        elif date_filter == "이번 주":
            start_of_week = today - timedelta(days=today.weekday())
            history_df = history_df[history_df['viewed_at'].dt.date >= start_of_week]
        elif date_filter == "이번 달":
            history_df = history_df[history_df['viewed_at'].dt.month == today.month]

        if category_filter == "뉴스만":
            history_df = history_df[history_df['content_type'] == 'article']
        elif category_filter == "영상만":
            history_df = history_df[history_df['content_type'] == 'video']

        st.markdown("━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        if st.button("🗑️ 전체 기록 삭제"):
            delete_all_history(conn, user_id)
            st.rerun()

        # Group by date
        for date, group in history_df.groupby(history_df['viewed_at'].dt.date):
            if date == today:
                st.subheader("오늘")
            elif date == today - timedelta(days=1):
                st.subheader("어제")
            else:
                st.subheader(date.strftime("%Y년 %m월 %d일"))

            for index, row in group.iterrows():
                col1, col2, col3 = st.columns([0.8, 0.1, 0.1])
                with col1:
                    icon = "📰" if row['content_type'] == 'article' else "🎬"
                    st.markdown(f"  • {icon} {row['title']} ({row['viewed_at'].strftime('%H:%M')})")
                with col2:
                    if st.button("❤️" if row['is_favorite'] else "🤍", key=f"fav_{row['id']}"):
                        toggle_favorite(conn, row['id'])
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"del_{row['id']}"):
                        delete_history_item(conn, row['id'])
                        st.rerun()
            st.markdown("")

    else:
        st.info("아직 시청 기록이 없습니다.")
else:
    st.error("사용자 정보를 불러오는 데 실패했습니다. 다시 로그인해주세요.")
