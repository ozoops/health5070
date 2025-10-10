
import streamlit as st

def set_background(image_url):
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap');
        
        body {{
            font-family: 'Nanum Gothic', sans-serif;
            font-size: 16px;
        }}
        
        [data-testid="stAppViewContainer"] {{
            background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("{image_url}");
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

        /* Hero Section */
        .hero-section, .content-section, .login-header {{
            background-color: rgba(0, 0, 0, 0.6) !important;
            backdrop-filter: blur(10px) !important;
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
        }}
        
        .hero-section {{
            text-align: center;
        }}

        .hero-section h1, .login-header h1 {{
            font-size: 3em;
            font-weight: 800;
            color: #ffffff;
            text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.7);
        }}
        .hero-section p, .login-header p {{
            font-size: 1.2em;
            color: #ffffff;
            text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.7);
            margin-bottom: 0;
        }}

        /* Content Section */
        .content-section:hover {{
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }}
        .content-section h2 {{
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
            color: #ffffff;
        }}
        .content-list-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid #555;
            color: #ffffff;
        }}
        .content-list-item:last-child {{
            border-bottom: none;
        }}
        .item-date {{
            font-size: 0.9em;
            color: #dddddd;
            margin-left: 1rem;
        }}

        /* Sidebar Hover Effect */
        [data-testid="stSidebarNav"] ul li a {{
            transition: transform 0.2s ease-in-out, background-color 0.2s ease-in-out;
            border-radius: 8px;
        }}
        [data-testid="stSidebarNav"] ul li a:hover {{
            transform: scale(1.05);
            background-color: rgba(255, 255, 255, 0.2) !important;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem 0;
            margin-top: 4rem;
            font-size: 1.1em;
            color: #ffffff;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
        }}

        /* --- Styled Form Elements (Theme-aware) --- */
        .stButton button {{
            font-weight: 700;
            border-radius: 8px;
            background-color: var(--primary-color);
            color: white;
        }}
        .stButton button:hover {{
            filter: brightness(1.2);
        }}

        /* --- Sidebar Logout Button --- */
        [data-testid="stSidebar"] .stButton button {{
            background-color: #e85d5d !important;
        }}
        [data-testid="stSidebar"] .stButton button:hover {{
            background-color: #c94f4f !important;
        }}
    </style>
    """, unsafe_allow_html=True)
