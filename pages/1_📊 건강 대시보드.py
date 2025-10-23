import streamlit as st
import pandas as pd
import altair as alt
import os
import sys
import json # Added import

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

# Load data from JSON file
data_file_path = os.path.join(project_root, "data", "dashboard_data.json")
with open(data_file_path, "r", encoding="utf-8") as f:
    dashboard_data = json.load(f)

def create_dashboard():
    st.markdown(
        """
        <style>
            .main-container.dashboard-container {
                margin-left: auto;
                margin-right: auto;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="main-container dashboard-container">', unsafe_allow_html=True)
    st.title("📊 5070 맞춤 건강 통계 대시보드")
    st.markdown("대한민국 50대부터 70대까지의 주요 건강 지표를 확인하고 건강 관리에 참고하세요.")
    st.markdown("---")

    # --- Key Metrics ---
    st.header("주요 건강 현황 (50-70대)")

    def create_gauge_chart(value, title, subtitle, color):
        subtitle_display = subtitle.replace(" / ", "\n")

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
            fontSize=52,
            fontWeight='bold',
            color='white', # Changed to white
            dy=-5 # Move it up slightly
        ).encode(
            text='text_value:N'
        )
        
        text_title = alt.Chart(pd.DataFrame({'value': [title]})).mark_text(
            align='center',
            baseline='middle', # Center it
            fontSize=20,
            fontWeight='bold',
            color='white', # Changed to white
            dy=55 # Position below the main value
        ).encode(
            text='value:N'
        )
        
        text_subtitle = alt.Chart(pd.DataFrame({'value': [subtitle_display]})).mark_text(
            align='center',
            baseline='middle', # Center it
            fontSize=14,
            color='#D3D3D3', # Lighter gray
            dy=95, # Position below the title
            lineHeight=18
        ).encode(
            text='value:N'
        )

        chart = (background + foreground + text_value + text_title + text_subtitle).properties(
            width=250,
            height=250
        ).configure_view(
            strokeWidth=0
        )
        return chart

    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        chart_data = dashboard_data["gauge_charts"][0]
        chart1 = create_gauge_chart(chart_data["value"], chart_data["title"], chart_data["subtitle"], chart_data["color"])
        st.altair_chart(chart1)
    with col2:
        chart_data = dashboard_data["gauge_charts"][1]
        chart2 = create_gauge_chart(chart_data["value"], chart_data["title"], chart_data["subtitle"], chart_data["color"])
        st.altair_chart(chart2)
    with col3:
        chart_data = dashboard_data["gauge_charts"][2]
        chart3 = create_gauge_chart(chart_data["value"], chart_data["title"], chart_data["subtitle"], chart_data["color"])
        st.altair_chart(chart3)

    st.markdown("---")

    # --- Charts ---
    st.header("연령대별 주요 사망 원인 (통계청, 2022년 기준)")

    # --- 50대 사망 원인 ---
    data_50s = pd.DataFrame(dashboard_data["mortality_data_50s"])
    data_50s = data_50s.rename(columns={
        "사망률 (인구 10만 명당, 2023년)": "사망률",
        "비고 (2023년 기준)": "비고"
    })
    chart_50s = alt.Chart(data_50s).mark_bar().encode(
        x=alt.X('사망률:Q', title='사망률 (인구 10만 명당, 2023년)'),
        y=alt.Y('사망 원인:N', sort='-x', title='사망 원인'),
        tooltip=['사망 원인', '사망률', '비고']
    ).properties(
        title='50대 주요 사망 원인'
    )

    # --- 70대 사망 원인 ---
    data_70s = pd.DataFrame(dashboard_data["mortality_data_70s"])
    data_70s = data_70s.rename(columns={
        "사망률 (인구 10만 명당, 2023년)": "사망률",
        "비고 (2023년 기준)": "비고"
    })
    chart_70s = alt.Chart(data_70s).mark_bar().encode(
        x=alt.X('사망률:Q', title='사망률 (인구 10만 명당, 2023년)'),
        y=alt.Y('사망 원인:N', sort='-x', title='사망 원인'),
        tooltip=['사망 원인', '사망률', '비고']
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
    chronic_data = pd.DataFrame(dashboard_data["chronic_disease_prevalence"])

    chronic_data_melted = chronic_data.melt('질환명', var_name='연령대', value_name='유병률 (%)')

    chart_chronic = alt.Chart(chronic_data_melted).mark_bar().encode(
        x=alt.X('연령대:N', title='연령대'),
        y=alt.Y('유병률 (%):Q', title='유병률 (%)'),
        color='연령대:N',
        row=alt.Row('질환명:N', header=alt.Header(titleOrient="bottom", labelOrient="bottom")),
        tooltip=['연령대', '질환명', '유병률 (%)']
    ).properties(
        title='연령대별 주요 만성질환 유병률 비교',
        height=100, # Height for each individual chart
        width=alt.Step(80) # Width for each individual chart
    )
    st.altair_chart(chart_chronic, use_container_width=True)
    st.markdown("""
    <div style="background-color: rgba(38, 139, 219, 0.2); border-left: 5px solid #268bdb; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;">
        <span style="color: white;">💡 위 통계는 일반적인 경향을 나타내며, 개인의 건강 상태는 다를 수 있습니다. 정기적인 건강검진과 전문가 상담이 중요합니다.</span>
    </div>
    """, unsafe_allow_html=True)


    st.markdown('</div>', unsafe_allow_html=True)
if __name__ == "__main__":
    create_dashboard()
