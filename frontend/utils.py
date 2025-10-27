import streamlit as st
import time

def set_background(image_url):
    cache_buster = int(time.time())
    # Check if the URL already has query parameters
    if '?' in image_url:
        image_url_with_buster = f"{image_url}&v={cache_buster}"
    else:
        image_url_with_buster = f"{image_url}?v={cache_buster}"
        
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap');
        
        body {{
            font-family: 'Nanum Gothic', sans-serif;
            font-size: 16px;
        }}
        
        [data-testid="stAppViewContainer"] {{
            background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("{image_url_with_buster}");
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

        /* --- Theme-aware containers --- */
        .hero-section, .content-section, .login-header {{
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            backdrop-filter: blur(10px) !important;
            border: 1px solid transparent;
        }}

        /* Light theme styles */
        .light-theme {
            --container-bg-color: rgba(240, 242, 246, 0.8);
            --container-border-color: var(--gray-30);
            --text-shadow: none;
        }

        /* Dark theme styles */
        .dark-theme {
            --container-bg-color: rgba(0, 0, 0, 0.6);
            --container-border-color: var(--gray-80);
            --text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
        }

        .hero-section {{
            text-align: center;
        }}

        .hero-section h1, .login-header h1, .content-section h2 {{
            color: var(--text-color);
        }}
        .hero-section p, .login-header p {{
            font-size: 1.2em;
            color: var(--text-color);
            opacity: 0.9;
            margin-bottom: 0;
        }}

        /* Content Section */
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
            border-bottom: 1px solid var(--gray-40);
            color: var(--text-color);
        }}
        .content-list-item:last-child {{
            border-bottom: none;
        }}
        .item-date {{
            font-size: 0.9em;
            color: var(--text-color);
            opacity: 0.7;
            margin-left: 1rem;
        }}

        /* Sidebar Hover Effect */
        [data-testid="stSidebarNav"] ul li a {{
            transition: transform 0.2s ease-in-out, background-color 0.2s ease-in-out;
            border-radius: 8px;
        }}
        [data-testid="stSidebarNav"] ul li a:hover {{
            transform: scale(1.25);
            background-color: var(--secondary-background-color);
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem 0;
            margin-top: 4rem;
            font-size: 1.1em;
            color: var(--text-color);
            opacity: 0.7;
        }}

        /* --- Styled Form Elements (Theme-aware) --- */
        .stButton button {{
            font-weight: 700;
            border-radius: 8px;
            background-color: var(--primary-color);
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

        /* --- Mobile Responsiveness --- */
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
                font-size: 0.8em;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)