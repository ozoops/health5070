
import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(os.path.join(__file__, '..', '..'))))
from backend.database import init_db, get_user, get_chat_history, delete_chat_history_item, delete_all_chat_history
from frontend.utils import set_background
from frontend.auth import is_logged_in

st.set_page_config(page_title="AI 상담 기록", layout="wide")
set_background("https://images.unsplash.com/photo-1589792939093-345341b4c48c?q=80&w=1974&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")

st.title("📜 AI 상담 기록")

if not is_logged_in():
    st.warning("📜 상담 기록은 로그인 후 이용 가능합니다.")
    st.info("왼쪽 사이드바에서 로그인 또는 회원가입을 해주세요.")
    st.stop()

conn = init_db()
user = get_user(conn, st.session_state['email'])

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
        st.info("아직 대화 기록이 없습니다.")
else:
    st.error("사용자 정보를 불러오는 데 실패했습니다. 다시 로그인해주세요.")

