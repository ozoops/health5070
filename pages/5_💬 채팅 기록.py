
import streamlit as st
import pandas as pd
import sys
import os
import pytz # Import pytz for timezone handling

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

        search_query = st.text_input("검색", placeholder="키워드를 입력하세요...", help="채팅 기록에서 키워드를 검색합니다.")

        # Filter chat history based on search query
        # We need to keep both user and assistant messages for the expander functionality
        # So, we'll filter the original chat_history and then process it.
        filtered_chat_history_with_responses = []
        for i, message in enumerate(chat_history):
            if search_query.lower() in message['content'].lower():
                filtered_chat_history_with_responses.append(message)
                # If the next message is an assistant response, include it too
                if i + 1 < len(chat_history) and chat_history[i+1]["role"] == "assistant":
                    filtered_chat_history_with_responses.append(chat_history[i+1])

        if st.button("🗑️ 전체 기록 삭제"):
            delete_all_chat_history(conn, user_id)
            st.rerun()

        if filtered_chat_history_with_responses:
            # Define the local timezone
            local_timezone = pytz.timezone('Asia/Seoul')

            # Display in reverse order (newest first)
            for i in range(len(filtered_chat_history_with_responses) - 1, -1, -1):
                message = filtered_chat_history_with_responses[i]
                
                if message["role"] == "user":
                    with st.chat_message("user"):
                        col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                        with col1:
                            st.markdown(message['content'])
                            # Find the corresponding assistant message
                            assistant_response_content = ""
                            original_chat_index = -1
                            for idx, original_msg in enumerate(chat_history):
                                if original_msg['id'] == message['id']:
                                    original_chat_index = idx
                                    break
                            
                            if original_chat_index != -1 and original_chat_index + 1 < len(chat_history):
                                next_message = chat_history[original_chat_index + 1]
                                if next_message["role"] == "assistant":
                                    assistant_response_content = next_message['content']

                            if assistant_response_content:
                                with st.expander("답변 보기"):
                                    st.markdown(assistant_response_content)
                        with col2:
                            timestamp_dt = pd.to_datetime(message['timestamp'])
                            # Convert to local timezone before formatting
                            timestamp_dt_local = timestamp_dt.tz_localize(pytz.utc).tz_convert(local_timezone)
                            st.caption(timestamp_dt_local.strftime("%Y-%m-%d %H:%M"))
                        with col3:
                            if st.button("🗑️", key=f"del_{message['id']}"):
                                delete_chat_history_item(conn, message['id'])
                                st.rerun()
        else:
            st.info("검색 결과가 없습니다.")
    else:
        st.info("아직 대화 기록이 없습니다.")
else:
    st.error("사용자 정보를 불러오는 데 실패했습니다. 다시 로그인해주세요.")

