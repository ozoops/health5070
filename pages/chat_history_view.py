import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(os.path.join(__file__, '..', '..'))))
from backend.database import init_db, get_user, get_chat_history, delete_chat_history_item, delete_all_chat_history
from frontend.utils import set_background

st.set_page_config(page_title="AI 상담 기록", layout="wide")
set_background("https://images.unsplash.com/photo-1589792939093-345341b4c48c?q=80&w=1974&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")

st.title("📜 AI 상담 기록")

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
        chat_history = get_chat_history(conn, user_id)

        if chat_history:
            st.markdown("━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            if st.button("🗑️ 전체 기록 삭제"):
                delete_all_chat_history(conn, user_id)
                st.rerun()

            for message in reversed(chat_history):
                with st.chat_message(message["role"]):
                    col1, col2 = st.columns([0.9, 0.1])
                    with col1:
                        st.markdown(message['content'])
                    with col2:
                        if st.button("🗑️", key=f"del_{message['id']}"):
                            delete_chat_history_item(conn, message['id'])
                            st.rerun()

        else:
            st.write("아직 대화 기록이 없습니다.")
    else:
        st.warning("사용자 정보를 찾을 수 없습니다.")
else:
    st.warning("로그인이 필요합니다.")
