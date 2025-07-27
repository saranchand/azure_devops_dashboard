import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from data.fetch_data import get_sprint_work_items, get_sprint_dates
from data.process_data import create_dataframe, calculate_metrics
from data.burndown import generate_burndown_and_burnup
from llm.analyze import get_ai_insights
from utils.helpers import (
    color_for_quality,
    color_for_effort_exceeded,
    color_for_lead_time
)
from configs.config import logger

def render_dashboard():
    st.set_page_config(page_title="Azure DevOps Sprint Dashboard", layout="wide")
    st.title("📊 Azure DevOps Sprint Dashboard")

    # Sprint Dates
    dates = get_sprint_dates()
    if dates:
        st.markdown(
            f"**Sprint Start:** {dates['start_date']}   "
            f"**End:** {dates['end_date']}"
        )

    # Fetch & process data
    try:
        with st.spinner("Loading sprint data..."):
            raw = get_sprint_work_items()
        if not raw:
            st.warning("⚠️ No work items found.")
            return

        df = create_dataframe(raw)
        if df.empty:
            st.error("❌ Data processing failed.")
            return

        metrics, df = calculate_metrics(df)
    except Exception as e:
        logger.exception("Dashboard load error")
        st.error("❌ Could not load data. See logs.")
        with st.expander("Error Details"):
            st.code(str(e))
        return

    # KPI Row
    est_issues = df[df["RemainingWork"] > df["OriginalEstimate"]]
    cols = st.columns(6)
    cols[0].metric("📦 Total Stories", metrics["total_stories"])
    cols[1].metric("🐞 Bugs in Stories", metrics["bugs_in_stories"])

    qc = color_for_quality(metrics["quality_percent"])
    cols[2].markdown(
        f"**✅ Quality**<br>"
        f"<span style='color:{qc}; font-size:20px'>"
        f"{metrics['quality_percent']}%</span>",
        unsafe_allow_html=True
    )

    ec = color_for_effort_exceeded(metrics["effort_exceeded_count"])
    cols[3].markdown(
        f"**⚠️ Effort Exceeded**<br>"
        f"<span style='color:{ec}; font-size:20px'>"
        f"{metrics['effort_exceeded_count']}</span>",
        unsafe_allow_html=True
    )

    lc = color_for_lead_time(metrics["average_lead_time"])
    cols[4].markdown(
        f"**⏱️ Lead Time**<br>"
        f"<span style='color:{lc}; font-size:20px'>"
        f"{metrics['average_lead_time']} days</span>",
        unsafe_allow_html=True
    )

    cols[5].metric(
        "👷 Engineers with Issues",
        len(est_issues["AssignedTo"].dropna().unique())
    )

    # Task Hours Worked Chart
    st.markdown("---")
    st.markdown("### 💼 Task Hours Worked")
    df_plot = df.copy()
    df_plot["HoursWorked"] = (df_plot["OriginalEstimate"] - df_plot["RemainingWork"]).clip(lower=0)
    df_plot = df_plot.sort_values("HoursWorked", ascending=False)
    df_plot["Over"] = df_plot["HoursWorked"] > df_plot["OriginalEstimate"]

    fig = px.bar(
        df_plot,
        x="HoursWorked",
        y="Title",
        orientation="h",
        color="Over",
        color_discrete_map={True: "crimson", False: "seagreen"},
        labels={"HoursWorked": "Hours Worked", "Title": "Work Item"},
        title="🏷️ Task Hours Worked (Red = Over Estimate)"
    )
    fig.update_traces(texttemplate="%{x:.1f}h", textposition="outside")
    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        margin=dict(l=200, r=40, t=60, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabs: Burndown, Burnup, AI, Raw Analysis
    tab1, tab2, tab3, tab4 = st.tabs([
        "📉 Burndown",
        "📈 Burnup",
        "🧠 AI Summary",
        "📋 Raw Analysis"
    ])

    with tab1:
        st.markdown("### Sprint Burndown Chart")
        bd = generate_burndown_and_burnup(df)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=bd["Date"], y=bd["ActualRemainingWork"],
            name="Actual Remaining", line=dict(color="red", width=3)
        ))
        fig1.add_trace(go.Scatter(
            x=bd["Date"], y=bd["IdealRemainingWork"],
            name="Ideal Remaining", line=dict(color="green", width=3, dash="dash")
        ))
        fig1.update_layout(
            xaxis_title="Date", yaxis_title="Hours Remaining",
            template="plotly_white", height=400
        )
        st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        st.markdown("### Sprint Burnup Chart")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=bd["Date"], y=bd["CompletedWork"],
            name="Completed Work", line=dict(color="blue", width=3)
        ))
        fig2.add_trace(go.Scatter(
            x=bd["Date"],
            y=[df["OriginalEstimate"].sum()] * len(bd),
            name="Total Scope", line=dict(color="black", width=2, dash="dot")
        ))
        fig2.update_layout(
            xaxis_title="Date", yaxis_title="Cumulative Hours",
            template="plotly_white", height=400
        )
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.markdown("### 🤖 AI Sprint Health Analysis")
