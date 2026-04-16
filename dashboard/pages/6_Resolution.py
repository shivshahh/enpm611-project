import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from metrics import resolution_metrics

st.header("Resolution Efficiency")

df_issues = st.session_state.get("df_issues")
df_events = st.session_state.get("df_events")

if df_issues is None:
    st.warning("Please load the dashboard from the main page first.")
    st.stop()

result = resolution_metrics(df_issues, df_events)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Median Days to Close", f"{result['median_days_to_close']}" if result["median_days_to_close"] else "N/A")
col2.metric("Reopen Rate", f"{result['reopen_rate']}%")
col3.metric("Closed This Month", f"{result['closed_this_month']:,}")
col4.metric("Net Open (This Month)", f"{result['net_open_this_month']:+,}")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Time to Close Distribution")
    close_days = df_issues["days_to_close"].dropna()
    if not close_days.empty:
        bins = [0, 1, 7, 28, 90, 365, float("inf")]
        bin_labels = ["<1d", "1-7d", "1-4w", "1-3mo", "3-12mo", ">1yr"]
        colors = ["#10b981", "#10b981", "#4a9eff", "#f59e0b", "#ef4444", "#7f1d1d"]
        counts, _ = np.histogram(close_days, bins=bins)
        fig_hist = go.Figure(data=[go.Bar(x=bin_labels, y=counts, marker_color=colors)])
        fig_hist.update_layout(template="plotly_dark", height=400, xaxis_title="Time to Close", yaxis_title="Issues")
        st.plotly_chart(fig_hist, use_container_width=True)

with col_right:
    st.subheader("Monthly Close vs Creation Rate")
    monthly = result["monthly_rates"]
    if not monthly.empty:
        fig_rate = go.Figure()
        fig_rate.add_trace(go.Scatter(x=monthly["month"], y=monthly["created"], mode="lines", name="Created", line=dict(color="#ef4444")))
        fig_rate.add_trace(go.Scatter(x=monthly["month"], y=monthly["closed"], mode="lines", name="Closed", line=dict(color="#10b981")))
        fig_rate.update_layout(template="plotly_dark", height=400, xaxis_title="Month", yaxis_title="Issues")
        st.plotly_chart(fig_rate, use_container_width=True)

st.subheader("Most Reopened Issues")
most_reopened = result["most_reopened"]
if not most_reopened.empty:
    display = most_reopened.copy()
    display["labels_str"] = display["labels"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")
    st.dataframe(
        display[["number", "title", "reopen_count", "labels_str", "state"]].rename(
            columns={"number": "#", "title": "Title", "reopen_count": "Reopens", "labels_str": "Labels", "state": "State"}
        ),
        use_container_width=True, hide_index=True,
    )
else:
    st.info("No reopened issues found.")
