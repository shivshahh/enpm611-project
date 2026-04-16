import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from metrics import staleness_metrics

st.header("Stale Issues")

df_issues = st.session_state.get("df_issues")

if df_issues is None:
    st.warning("Please load the dashboard from the main page first.")
    st.stop()

result = staleness_metrics(df_issues)

col1, col2, col3 = st.columns(3)
col1.metric("Stale Issues (>90d idle)", f"{result['stale_count']:,}")
col2.metric("Zombie Issues (>1yr idle)", f"{result['zombie_count']:,}")
col3.metric("No Response Ever", f"{result['no_response_count']:,}")

st.subheader("Open Issues by Last Activity")
dist = result["bucket_distribution"]
buckets = ["Active", "Aging", "Stale", "Zombie"]
colors = {"Active": "#10b981", "Aging": "#f59e0b", "Stale": "#ef4444", "Zombie": "#7f1d1d"}
values = [dist.get(b, 0) for b in buckets]
total = sum(values)

if total > 0:
    fig_bar = go.Figure()
    for bucket, val in zip(buckets, values):
        pct = round(val / total * 100, 1)
        fig_bar.add_trace(go.Bar(
            x=[val], y=["Issues"], orientation="h",
            name=f"{bucket} ({pct}%)",
            marker_color=colors[bucket],
            text=f"{bucket}: {val}",
            textposition="inside",
        ))
    fig_bar.update_layout(
        barmode="stack", template="plotly_dark", height=120,
        showlegend=True, yaxis_visible=False,
        margin=dict(l=0, r=0, t=0, b=0),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Issues Needing Attention")
attention = result["attention_list"]

if not attention.empty:
    display = attention.copy()
    display["days_idle"] = display["days_since_last_activity"].round(0).astype(int)
    display["labels_str"] = display["labels"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")
    display["last_activity_str"] = display["last_activity"].dt.strftime("%Y-%m-%d")
    st.dataframe(
        display[["number", "title", "labels_str", "last_activity_str", "days_idle", "staleness_bucket"]].rename(
            columns={
                "number": "#", "title": "Title", "labels_str": "Labels",
                "last_activity_str": "Last Activity", "days_idle": "Days Idle",
                "staleness_bucket": "Status",
            }
        ),
        use_container_width=True, hide_index=True,
    )
else:
    st.success("No stale issues found!")
