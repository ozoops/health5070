import streamlit as st
import time
from typing import Dict, Optional


def _get_theme_palette(theme_mode: str) -> Dict[str, str]:
    """Return color palette tokens for the given theme mode."""
    if theme_mode == "light":
        return {
            "overlay": "rgba(255, 255, 255, 0.65)",
            "container_bg": "rgba(255, 255, 255, 0.85)",
            "container_border": "rgba(0, 0, 0, 0.12)",
            "text_color": "#1f2933",
            "muted_text": "rgba(31, 41, 51, 0.72)",
            "text_shadow": "none",
            "primary": "#1d6ed8",
            "primary_hover": "#1555a4",
            "secondary_bg": "rgba(0, 0, 0, 0.08)",
            "input_bg": "rgba(255, 255, 255, 0.92)",
            "input_border": "rgba(0, 0, 0, 0.18)",
            "input_text": "#1f2933",
        }
    return {
        "overlay": "rgba(0, 0, 0, 0.68)",
        "container_bg": "rgba(17, 25, 40, 0.78)",
        "container_border": "rgba(148, 163, 184, 0.35)",
        "text_color": "#f5f7fa",
        "muted_text": "rgba(203, 213, 225, 0.85)",
        "text_shadow": "1px 1px 4px rgba(0, 0, 0, 0.45)",
        "primary": "#4f9dff",
        "primary_hover": "#3c7bcc",
        "secondary_bg": "rgba(255, 255, 255, 0.12)",
        "input_bg": "rgba(15, 23, 42, 0.85)",
        "input_border": "rgba(148, 163, 184, 0.35)",
        "input_text": "#f8fafc",
    }


def get_theme_mode(default: str = "dark") -> str:
    """Return the current theme mode stored in session state."""
    return st.session_state.get("theme_mode", default)


def render_theme_selector(default: Optional[str] = None) -> str:
    """Render a sidebar selector for switching between light and dark themes."""
    if "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = default or "dark"

    label_to_mode = {
        "🌞 라이트 모드": "light",
        "🌙 다크 모드": "dark",
    }
    options = list(label_to_mode.keys())
    current_label = next(
        label for label, mode in label_to_mode.items() if mode == st.session_state["theme_mode"]
    )

    selected_label = st.sidebar.radio(
        "화면 모드",
        options,
        index=options.index(current_label),
        key="theme_mode_selector",
    )
    selected_mode = label_to_mode[selected_label]
    st.session_state["theme_mode"] = selected_mode
    return selected_mode


def set_background(image_url: str, theme_mode: Optional[str] = None) -> None:
    """Apply background image and theme-aware styling."""
    if theme_mode is None:
        theme_mode = get_theme_mode()

    palette = _get_theme_palette(theme_mode)
    cache_buster = int(time.time())

    if "?" in image_url:
        image_url_with_buster = f"{image_url}&v={cache_buster}"
    else:
        image_url_with_buster = f"{image_url}?v={cache_buster}"

    st.markdown(
        f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap');

        body, .stApp {{
            font-family: 'Nanum Gothic', sans-serif;
            font-size: 16px;
            color: var(--text-color);
        }}

        :root {{
            --container-bg-color: {palette["container_bg"]};
            --container-border-color: {palette["container_border"]};
            --text-shadow: {palette["text_shadow"]};
            --text-color: {palette["text_color"]};
            --muted-text-color: {palette["muted_text"]};
            --primary-color: {palette["primary"]};
            --primary-color-hover: {palette["primary_hover"]};
            --secondary-background-color: {palette["secondary_bg"]};
            --input-bg-color: {palette["input_bg"]};
            --input-border-color: {palette["input_border"]};
            --input-text-color: {palette["input_text"]};
        }}

        [data-testid="stAppViewContainer"] {{
            background-image: linear-gradient({palette["overlay"]}, {palette["overlay"]}), url("{image_url_with_buster}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        [data-testid="stHeader"] {{
            background-color: rgba(0,0,0,0);
        }}

        [data-testid="stToolbar"] {{
            right: 2rem;
        }}

        .main-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 1rem;
        }}

        .hero-section, .content-section, .login-header {{
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            backdrop-filter: blur(10px) !important;
            border: 1px solid var(--container-border-color);
            background-color: var(--container-bg-color) !important;
            color: var(--text-color);
        }}

        .hero-section {{
            text-align: center;
        }}

        .hero-section h1, .login-header h1, .content-section h2 {{
            color: var(--text-color);
            text-shadow: var(--text-shadow);
        }}
        .hero-section p, .login-header p {{
            font-size: 1.2em;
            color: var(--muted-text-color);
            margin-bottom: 0;
        }}

        .content-section:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        .content-section h2 {{
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }}
        .content-list-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--primary-color-hover);
            color: var(--text-color);
        }}
        .content-list-item:last-child {{
            border-bottom: none;
        }}
        .item-date {{
            font-size: 0.9em;
            color: var(--muted-text-color);
            margin-left: 1rem;
        }}

        body a {{
            color: var(--primary-color);
        }}

        [data-testid="stSidebarNav"] ul li a {{
            transition: transform 0.2s ease-in-out, background-color 0.2s ease-in-out;
            border-radius: 8px;
        }}
        [data-testid="stSidebarNav"] ul li a:hover {{
            transform: scale(1.15);
            background-color: var(--secondary-background-color);
        }}
        [data-testid="stSidebarNav"] ul li a[href*="app_article"] {{
            display: none !important;
        }}
        [data-testid="stSidebarNav"] ul li a[href*="9_%F0%9F%94%92"] {{
            display: none !important;
        }}
        [data-testid="stSidebarNav"] ul li a[href*="9_🔒_관리자"] {{
            display: none !important;
        }}
        [data-testid="stSidebarNav"] ul li a[href*="_9_%F0%9F%94%92"] {{
            display: none !important;
        }}
        [data-testid="stSidebarNav"] ul li a[href*="_9_🔒_관리자"] {{
            display: none !important;
        }}

        .footer {{
            text-align: center;
            padding: 2rem 0;
            margin-top: 4rem;
            font-size: 1.1em;
            color: var(--muted-text-color);
        }}

        .sidebar-contact-button {{
            display: block;
            width: 100%;
            text-align: center;
            margin-top: 0.5rem;
        }}

        .stButton button {{
            font-weight: 700;
            border-radius: 8px;
            background-color: var(--primary-color);
            color: #ffffff;
            border: none;
        }}
        .stButton button:hover {{
            background-color: var(--primary-color-hover);
        }}

        [data-testid="stSidebar"] .stButton button {{
            background-color: #e85d5d !important;
            color: #ffffff !important;
        }}
        [data-testid="stSidebar"] .stButton button:hover {{
            background-color: #c94f4f !important;
        }}

        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div:first-child,
        .stMultiSelect div[data-baseweb="select"] > div:first-child,
        .stNumberInput input {{
            background-color: var(--input-bg-color);
            color: var(--input-text-color);
            border: 1px solid var(--input-border-color);
        }}

        .stRadio label,
        .stSelectbox label,
        .stTextInput label,
        .stTextArea label,
        .stMultiSelect label,
        .stNumberInput label {{
            color: var(--text-color);
        }}

        @media (max-width: 768px) {{
            .main-container {{
                padding: 0.5rem;
            }}
            .hero-section, .content-section, .login-header {{
                padding: 1rem;
                margin-bottom: 1rem;
            }}
            .hero-section h1, .login-header h1 {{
                font-size: 1.8em;
            }}
            .hero-section p, .login-header p {{
                font-size: 1em;
            }}
            .content-section h2 {{
                font-size: 1.5em;
            }}
            .content-list-item {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .item-date {{
                margin-left: 0;
                margin-top: 0.25rem;
                font-size: 0.85em;
            }}
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )
