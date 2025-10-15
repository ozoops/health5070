import streamlit as st
import pandas as pd
import altair as alt
import os
import sys

# Add project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from frontend.utils import set_background

# Set background image
set_background("https://images.unsplash.com/photo-1576091160550-2173dba999ef?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")

def nanum_gothic_theme():
    return {
        "config": {
            "title": {"font": "Nanum Gothic", "anchor": "middle"},
            "axis": {"labelFont": "Nanum Gothic", "titleFont": "Nanum Gothic"},
            "header": {"labelFont": "Nanum Gothic", "titleFont": "Nanum Gothic"},
            "legend": {"labelFont": "Nanum Gothic", "titleFont": "Nanum Gothic"},
            "range": {
                "category": {"scheme": "pastel1"},
                "diverging": {"scheme": "redblue"},
                "heatmap": {"scheme": "viridis"},
                "ramp": {"scheme": "blues"},
            },
            "view": {"stroke": "transparent"},
        }
    }

alt.themes.register("nanum_gothic", nanum_gothic_theme)
alt.themes.enable("nanum_gothic")


def create_dashboard():
    # st.set_page_config(layout="wide") # This is now set globally or in the main app
    st.title("📊 5070 맞춤 건강 통계 대시보드")
    st.markdown("대한민국 50대부터 70대까지의 주요 건강 지표를 확인하고 건강 관리에 참고하세요.")
    st.markdown("---")

    # --- Key Metrics ---
    st.header("주요 건강 현황 (50-70대)")

    def create_gauge_chart(value, title, subtitle, color):
        source = pd.DataFrame({
            "value": [value],
            "text_value": [f'{value:.1f}%']
        })

        background = alt.Chart(pd.DataFrame({'value': [100]})).mark_arc(
            innerRadius=80,
            outerRadius=120,
            color='#555555' # Darker background for the arc
        ).encode(
            theta=alt.Theta("value:Q", stack=True, scale=alt.Scale(domain=[0, 100])),
        )

        foreground = alt.Chart(source).mark_arc(
            innerRadius=80,
            outerRadius=120,
        ).encode(
            theta=alt.Theta("value:Q", stack=True),
            color=alt.Color(value=color)
        )

        text_value = alt.Chart(source).mark_text(
            align='center',
            baseline='middle',
            fontSize=45,
            fontWeight='bold',
            color='white', # Changed to white
            dy=-10 # Move it up slightly
        ).encode(
            text='text_value:N'
        )
        
        text_title = alt.Chart(pd.DataFrame({'value': [title]})).mark_text(
            align='center',
            baseline='middle', # Center it
            fontSize=18,
            fontWeight='bold',
            color='white', # Changed to white
            dy=40 # Position below the main value
        ).encode(
            text='value:N'
        )
        
        text_subtitle = alt.Chart(pd.DataFrame({'value': [subtitle]})).mark_text(
            align='center',
            baseline='middle', # Center it
            fontSize=14,
            color='#D3D3D3', # Lighter gray
            dy=70 # Position below the title
        ).encode(
            text='value:N'
        )

        chart = (background + foreground + text_value + text_title + text_subtitle).properties(
            width=300,
            height=300
        ).configure_view(
            strokeWidth=0
        )
        return chart

    col1, col2, col3 = st.columns(3)
    with col1:
        chart1 = create_gauge_chart(87, "70세 이상 만성질환 보유율", "10명 중 약 9명", "#FF4B4B")
        st.altair_chart(chart1, use_container_width=True)
    with col2:
        chart2 = create_gauge_chart(28.3, "60대 당뇨 유병률", "4명 중 1명 이상", "#FFC300")
        st.altair_chart(chart2, use_container_width=True)
    with col3:
        chart3 = create_gauge_chart(64.3, "70세 이상 여성 고혈압 유병률", "3명 중 2명", "#4B79FF")
        st.altair_chart(chart3, use_container_width=True)

    st.caption("데이터 출처: 통계청, 국민건강보험공단 등 최신 건강 통계 자료 (2023-2024)")
    st.markdown("---")

    # --- Charts ---
    st.header("연령대별 주요 사망 원인 (통계청, 2022년 기준)")

    # --- 50대 사망 원인 ---
    data_50s = pd.DataFrame({
        '사망 원인': ['암 (간암)', '자살', '심장 질환', '뇌혈관 질환'],
        '사망률 (인구 10만 명당)': [95.6, 28.9, 25.1, 20.5]
    })
    chart_50s = alt.Chart(data_50s).mark_bar().encode(
        x=alt.X('사망률 (인구 10만 명당):Q', title='사망률 (인구 10만 명당)'),
        y=alt.Y('사망 원인:N', sort='-x', title='사망 원인'),
        tooltip=['사망 원인', '사망률 (인구 10만 명당)']
    ).properties(
        title='50대 주요 사망 원인'
    )

    # --- 70대 사망 원인 ---
    data_70s = pd.DataFrame({
        '사망 원인': ['암 (폐암)', '심장 질환', '뇌혈관 질환', '폐렴', '알츠하이머병'],
        '사망률 (인구 10만 명당)': [444.5, 189.2, 120.1, 115.7, 78.9]
    })
    chart_70s = alt.Chart(data_70s).mark_bar().encode(
        x=alt.X('사망률 (인구 10만 명당):Q', title='사망률 (인구 10만 명당)'),
        y=alt.Y('사망 원인:N', sort='-x', title='사망 원인'),
        tooltip=['사망 원인', '사망률 (인구 10만 명당)']
    ).properties(
        title='70대 주요 사망 원인'
    )

    c1, c2 = st.columns(2)
    with c1:
        st.altair_chart(chart_50s, use_container_width=True)
    with c2:
        st.altair_chart(chart_70s, use_container_width=True)

    st.markdown("---")

    # --- 만성질환 유병률 ---
    st.header("주요 만성질환 유병률 (2023년 기준)")
    chronic_data = pd.DataFrame({
        '질환명': ['고혈압', '당뇨병', '만성콩팥병', '비만(남성)'],
        '50대': [35.8, 19.7, 10.1, 48.1],
        '60대': [55.4, 28.3, 15.5, 39.7],
        '70대 이상': [68.1, 31.2, 25.1, 28.5]
    })

    chronic_data_melted = chronic_data.melt('질환명', var_name='연령대', value_name='유병률 (%)')

    chart_chronic = alt.Chart(chronic_data_melted).mark_bar().encode(
        x=alt.X('연령대:N', title='연령대'),
        y=alt.Y('유병률 (%):Q', title='유병률 (%)'),
        color='연령대:N',
        column='질환명:N',
        tooltip=['연령대', '질환명', '유병률 (%)']
    ).properties(
        title='연령대별 주요 만성질환 유병률 비교'
    )
    st.altair_chart(chart_chronic, use_container_width=True)
    st.markdown("""
    <div style="background-color: rgba(38, 139, 219, 0.2); border-left: 5px solid #268bdb; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;">
        <span style="color: white;">💡 위 통계는 일반적인 경향을 나타내며, 개인의 건강 상태는 다를 수 있습니다. 정기적인 건강검진과 전문가 상담이 중요합니다.</span>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    create_dashboard()