import streamlit as st

from frontend.app_article import main


def render_page() -> None:
    """Delegate rendering to the shared article/video viewer."""
    main()


if __name__ == "__main__":
    st.set_page_config(page_title="헬스케어 5070 - 기사/영상 보기")
    render_page()
else:
    render_page()
