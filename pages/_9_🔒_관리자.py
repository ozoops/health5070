import os
import sys
import streamlit as st

# Ensure project root on path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from frontend.admin_portal import render_admin_portal
from frontend.utils import set_background, render_theme_selector

st.set_page_config(page_title="🔒 관리자 모드", layout="wide")

theme_mode = render_theme_selector()
set_background(
    "https://images.unsplash.com/photo-1523875194681-bedd468c58bf?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    theme_mode=theme_mode,
)

st.markdown('<div class="main-container">', unsafe_allow_html=True)
st.title("🔒 관리자 전용 포털")
st.info("관리자 비밀번호를 입력하면 전체 기능을 사용할 수 있습니다.")
render_admin_portal()
st.markdown("</div>", unsafe_allow_html=True)
