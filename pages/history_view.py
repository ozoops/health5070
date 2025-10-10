import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(os.path.join(__file__, '..', '..'))))
from backend.database import get_view_history, init_db, get_user, toggle_favorite, delete_history_item, delete_all_history
from frontend.utils import set_background

st.set_page_config(page_title="시청 기록", layout="wide")
set_background("https://images.unsplash.com/photo-1526069974399-bf103a3abc9e?q=80&w=1974&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")

st.title("📋 시청 기록")

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

conn = init_db()
if 'username' in st.session_state and st.session_state['username']:
    user = get_user(conn, st.session_state['username'])
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
            st.write("아직 시청 기록이 없습니다.")
    else:
        st.warning("사용자 정보를 찾을 수 없습니다.")
else:
    st.warning("로그인이 필요합니다.")
