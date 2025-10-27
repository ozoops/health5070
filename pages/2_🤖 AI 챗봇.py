
import streamlit as st
import os
import sys

# --- Voice Input (Optional) ---
try:
    import speech_recognition as sr
    SPEECH_REC_AVAILABLE = True
except ImportError:
    SPEECH_REC_AVAILABLE = False

# Add project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.database import init_db, get_user, save_chat_message, get_chat_history
from frontend.utils import set_background, render_theme_selector
from frontend.auth import is_logged_in
from backend.article_generator import ArticleGenerator # Import our new Agent

# --- PAGE SETUP AND AUTH CHECK ---
st.set_page_config(page_title="AI 건강 비서", layout="centered")
theme_mode = render_theme_selector()
set_background(
    "https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    theme_mode=theme_mode,
)

if not is_logged_in():
    st.warning("🤖 AI 상담은 로그인 후 이용 가능합니다.")
    st.info("왼쪽 사이드바에서 로그인 또는 회원가입을 해주세요.")
    st.stop()

# --- DB and User Setup ---
conn = init_db()
user = get_user(conn, st.session_state['email'])
user_id = user['id']

# --- Voice Input Function ---
def get_voice_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("음성 입력을 시작하세요...")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            with st.spinner("음성을 텍스트로 변환 중..."):
                text = r.recognize_google(audio, language='ko-KR')
            st.session_state.voice_input = text
            st.rerun()
        except sr.WaitTimeoutError:
            st.warning("입력 시간이 초과되었습니다. 다시 시도해주세요.")
        except sr.UnknownValueError:
            st.error("음성을 인식할 수 없습니다. 더 명확하게 말씀해주세요.")
        except Exception as e:
            st.error(f"음성 인식 중 오류가 발생했습니다: {e}")
    return None

# --- Cache the Agent ---
@st.cache_resource
def get_article_agent():
    """Create and cache the ArticleGenerator agent."""
    return ArticleGenerator()

agent = get_article_agent()

# --- MAIN CONTENT ---
st.title("🤖 AI 건강 비서 (RAG Agent)")
st.markdown("""데이터베이스의 건강 기사를 검색하여 답변하는 RAG Agent입니다. 
예: '허리 디스크에 좋은 운동 알려줘'""")

# --- CHATBOT IMPLEMENTATION ---
# Initialize chat history
if "chat_messages" not in st.session_state:
    db_history = get_chat_history(conn, user_id)
    if db_history:
        st.session_state.chat_messages = db_history
    else:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "안녕하세요! 저는 헬스케어 5070 비서입니다. 데이터베이스에 저장된 건강 기사를 바탕으로 질문에 답변해 드립니다. 무엇이든 물어보세요."}
        ]

# Display chat messages from history on app rerun
for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle voice input if available
if st.session_state.get("voice_input"):
    prompt = st.session_state.pop("voice_input")
else:
    prompt = st.chat_input("건강에 대해 궁금한 점을 물어보세요.")

# Add voice input button
col1, col2 = st.columns([4,1])
with col2:
    if SPEECH_REC_AVAILABLE:
        if st.button("🎤 음성 질문"):
            get_voice_input()
    else:
        st.warning("음성 인식을 사용하려면 `SpeechRecognition`과 `PyAudio`를 설치하세요.", icon="⚠️")

# Accept user input
if prompt:
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    save_chat_message(conn, user_id, "user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent가 생각하고 검색하는 중..."):
            try:
                agent_history = []
                for msg in st.session_state.chat_messages:
                    if msg['role'] == 'user':
                        agent_history.append(("user", msg['content']))
                    elif msg['role'] == 'assistant':
                        agent_history.append(("ai", msg['content']))

                response = agent.run_agent(user_input=prompt, chat_history=agent_history)
                st.markdown(response)
                
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
                save_chat_message(conn, user_id, "assistant", response)

            except Exception as e:
                error_message = f"오류가 발생했습니다: {e}"
                st.error(error_message)
                st.session_state.chat_messages.append({"role": "assistant", "content": error_message})
                save_chat_message(conn, user_id, "assistant", error_message)
