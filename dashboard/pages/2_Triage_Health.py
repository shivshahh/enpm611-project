import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from metrics import triage_metrics

st.header("Triage Health")

df_issues = st.session_state.get("df_issues")
df_events = st.session_state.get("df_events")

if df_issues is None:
    st.warning("Please load the dashboard from the main page first.")
    st.stop()

result = triage_metrics(df_issues, df_events)

col1, col2, col3 = st.columns(3)
col1.metric("Median First Response", f"{result['median_first_response_days']} days" if result["median_first_response_days"] is not None else "N/A")
col2.metric("Median Time to Label", f"{result['median_time_to_label_days']} days" if result["median_time_to_label_days"] is not None else "N/A")
col3.metric("Unlabeled Issues", f"{result['unlabeled_count']:,}")

st.subheader("First Response Time Distribution")
response_times = df_issues["time_to_first_response"].dropna()

if not response_times.empty:
    bins = [0, 1/24, 0.25, 1, 3, 7, 14, 30, 90, 180, float("inf")]
    bin_labels = ["<1h", "1-6h", "6-24h", "1-3d", "3-7d", "1-2w", "2-4w", "1-3mo", "3-6mo", ">6mo"]
    colors = ["#10b981", "#10b981", "#10b981", "#10b981", "#f59e0b", "#f59e0b", "#ef4444", "#ef4444", "#ef4444", "#ef4444"]
    counts, _ = np.histogram(response_times, bins=bins)
    fig_hist = go.Figure(data=[go.Bar(x=bin_labels, y=counts, marker_color=colors)])
    fig_hist.update_layout(template="plotly_dark", height=400, xaxis_title="Response Time", yaxis_title="Number of Issues")
    st.plotly_chart(fig_hist, use_container_width=True)
else:
    st.info("No response time data available.")

st.subheader("Median First-Response Time by Issue Creation Month")
df_with_response = df_issues[df_issues["time_to_first_response"].notna()].copy()

if not df_with_response.empty:
    df_with_response["year_month"] = df_with_response["created_date"].dt.to_period("M")
    monthly_median_hours = df_with_response.groupby("year_month")["time_to_first_response"].median() * 24
    monthly_median_hours.index = monthly_median_hours.index.to_timestamp()
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=monthly_median_hours.index, y=monthly_median_hours.values, mode="lines", name="Median Response Time (hours)", line=dict(color="#4a9eff")))
    fig_trend.update_layout(template="plotly_dark", height=350, xaxis_title="Month", yaxis_title="Hours")
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("No triage trend data available.")
