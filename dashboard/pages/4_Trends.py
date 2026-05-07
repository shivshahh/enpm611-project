import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from metrics import trend_metrics

st.header("Bug vs Feature Trends")

df_issues = st.session_state.get("df_issues")

if df_issues is None:
    st.warning("Please load the dashboard from the main page first.")
    st.stop()

result = trend_metrics(df_issues)

col1, col2, col3 = st.columns(3)
col1.metric("Bug Issues", f"{result['bug_count']:,}")
col2.metric("Feature Requests", f"{result['feature_count']:,}")
col3.metric("Bug:Feature Ratio", f"{result['bug_feature_ratio']}")

st.subheader("Issue Type Trends (Monthly)")
monthly = result["monthly_trends"]

if not monthly.empty:
    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(x=monthly["month"], y=monthly["bugs"], mode="lines", name="Bugs", fill="tozeroy", line=dict(color="#ef4444"), fillcolor="rgba(239,68,68,0.3)"))
    fig_area.add_trace(go.Scatter(x=monthly["month"], y=monthly["features"], mode="lines", name="Features", fill="tozeroy", line=dict(color="#8b5cf6"), fillcolor="rgba(139,92,246,0.3)"))
    fig_area.update_layout(template="plotly_dark", height=450, xaxis_title="Month", yaxis_title="Issues")
    st.plotly_chart(fig_area, use_container_width=True)

st.subheader("Fastest Growing Categories (Last 12 Months vs Prior 12 Months)")
growth_df = result["label_growth"]

if not growth_df.empty:
    display_df = growth_df.head(15)[["label", "recent_count", "prior_count", "growth_pct"]].copy()
    display_df.columns = ["Label", "Last 12 Months", "Prior 12 Months", "Growth %"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("Not enough data for growth analysis.")
