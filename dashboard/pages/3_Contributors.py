import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from metrics import contributor_metrics

st.header("Contributors")

df_issues = st.session_state.get("df_issues")
df_events = st.session_state.get("df_events")

if df_issues is None:
    st.warning("Please load the dashboard from the main page first.")
    st.stop()

result = contributor_metrics(df_issues, df_events)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Contributors", f"{result['total_contributors']:,}")
col2.metric("Active (90d)", f"{result['active_90d']:,}")
col3.metric("New This Month", f"{result['new_this_month']:,}")
col4.metric("Returning", f"{result['returning']:,}")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Top Contributors (by events)")
    top_df = result["top_contributors"]
    st.dataframe(top_df, use_container_width=True, hide_index=True)

with col_right:
    st.subheader("New vs Returning Contributors (Monthly)")
    now = pd.Timestamp.now(tz="UTC")
    if not df_events.empty:
        all_authors = pd.concat([
            df_issues[["creator", "created_date"]].rename(columns={"creator": "author", "created_date": "date"}),
            df_events[["author", "event_date"]].rename(columns={"event_date": "date"}),
        ])
    else:
        all_authors = df_issues[["creator", "created_date"]].rename(columns={"creator": "author", "created_date": "date"})

    all_authors = all_authors[all_authors["author"] != ""]
    all_authors["year_month"] = all_authors["date"].dt.to_period("M")
    first_month = all_authors.groupby("author")["year_month"].min().rename("first_month")
    monthly_active = all_authors.groupby("year_month")["author"].nunique().rename("total")
    monthly_new = all_authors.merge(first_month, on="author")
    monthly_new = monthly_new[monthly_new["year_month"] == monthly_new["first_month"]]
    monthly_new_counts = monthly_new.groupby("year_month")["author"].nunique().rename("new")
    monthly_chart = pd.concat([monthly_active, monthly_new_counts], axis=1).fillna(0).astype(int)
    monthly_chart["returning"] = monthly_chart["total"] - monthly_chart["new"]
    monthly_chart.index = monthly_chart.index.to_timestamp()
    monthly_chart = monthly_chart.tail(12)

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=monthly_chart.index, y=monthly_chart["new"], name="New", marker_color="#10b981"))
    fig_bar.add_trace(go.Bar(x=monthly_chart.index, y=monthly_chart["returning"], name="Returning", marker_color="#4a9eff"))
    fig_bar.update_layout(barmode="stack", template="plotly_dark", height=400, xaxis_title="Month", yaxis_title="Contributors")
    st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Contributor Activity Heatmap (Top 15)")
if not df_events.empty:
    top_users = result["top_contributors"]["user"].head(15).tolist()
    heatmap_events = df_events[df_events["author"].isin(top_users)].copy()
    heatmap_events["year_month"] = heatmap_events["event_date"].dt.to_period("M")
    pivot = heatmap_events.groupby(["author", "year_month"]).size().unstack(fill_value=0)
    pivot = pivot[pivot.columns[-12:]] if len(pivot.columns) > 12 else pivot
    pivot.columns = pivot.columns.to_timestamp().strftime("%b %Y")
    fig_heat = px.imshow(pivot, labels=dict(x="Month", y="Contributor", color="Events"), color_continuous_scale="Greens", aspect="auto")
    fig_heat.update_layout(template="plotly_dark", height=max(300, len(top_users) * 30))
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("No event data available for heatmap.")
