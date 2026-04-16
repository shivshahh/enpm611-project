import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.header("Overview")

df_issues = st.session_state.get("df_issues")
df_events = st.session_state.get("df_events")

if df_issues is None:
    st.warning("Please load the dashboard from the main page first.")
    st.stop()

total = len(df_issues)
open_count = int((df_issues["state"] == "open").sum())
open_rate = round(open_count / total * 100, 1) if total > 0 else 0
avg_days_close = df_issues["days_to_close"].mean()

now = pd.Timestamp.now(tz="UTC")
ninety_days_ago = now - pd.Timedelta(days=90)
active_creators = set(df_issues[df_issues["created_date"] >= ninety_days_ago]["creator"].dropna().unique())
active_event_authors = set()
if df_events is not None and not df_events.empty:
    active_event_authors = set(df_events[df_events["event_date"] >= ninety_days_ago]["author"].dropna().unique())
active_contributors = len((active_creators | active_event_authors) - {""})

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Issues", f"{total:,}")
col2.metric("Open Issues", f"{open_count:,}", f"{open_rate}% open rate")
col3.metric("Avg Days to Close", f"{avg_days_close:.1f}" if pd.notna(avg_days_close) else "N/A")
col4.metric("Active Contributors (90d)", f"{active_contributors:,}")

st.subheader("Issues Over Time (Created vs Closed)")
df_copy = df_issues.copy()
df_copy["year_month"] = df_copy["created_date"].dt.to_period("M")
monthly_created = df_copy.groupby("year_month").size().rename("Created")
closed = df_copy[df_copy["state"] == "closed"]
monthly_closed = closed.groupby(closed["updated_date"].dt.to_period("M")).size().rename("Closed")
monthly = pd.concat([monthly_created, monthly_closed], axis=1).fillna(0).astype(int)
monthly.index = monthly.index.to_timestamp()

fig_line = go.Figure()
fig_line.add_trace(go.Scatter(x=monthly.index, y=monthly["Created"], mode="lines", name="Created", line=dict(color="#4a9eff")))
fig_line.add_trace(go.Scatter(x=monthly.index, y=monthly["Closed"], mode="lines", name="Closed", line=dict(color="#10b981")))
fig_line.update_layout(template="plotly_dark", height=400, xaxis_title="Month", yaxis_title="Issues")
st.plotly_chart(fig_line, use_container_width=True)

col_left, col_right = st.columns([2, 1])
with col_right:
    st.subheader("Issue State Breakdown")
    closed_count = total - open_count
    fig_donut = go.Figure(data=[go.Pie(
        labels=["Closed", "Open"],
        values=[closed_count, open_count],
        hole=0.5,
        marker_colors=["#10b981", "#f59e0b"],
    )])
    fig_donut.update_layout(template="plotly_dark", height=350)
    st.plotly_chart(fig_donut, use_container_width=True)
