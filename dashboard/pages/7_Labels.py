import streamlit as st
import plotly.express as px
import pandas as pd
from metrics import label_metrics

st.header("Label / Category Analysis")

df_issues = st.session_state.get("df_issues")

if df_issues is None:
    st.warning("Please load the dashboard from the main page first.")
    st.stop()

result = label_metrics(df_issues)

col1, col2, col3 = st.columns(3)
col1.metric("Unique Labels", f"{result['unique_labels']:,}")
col2.metric("Avg Labels per Issue", f"{result['avg_labels_per_issue']}")
col3.metric("Unlabeled Issues", f"{result['unlabeled_count']:,}")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Label Distribution")
    label_counts = result["label_counts"]
    if not label_counts.empty:
        top_labels = label_counts.head(30)
        fig_tree = px.treemap(top_labels, path=["label"], values="count", color="count", color_continuous_scale="RdYlGn_r")
        fig_tree.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig_tree, use_container_width=True)

with col_right:
    st.subheader("Label Co-occurrence")
    co_occurrence = result["co_occurrence"]
    if not co_occurrence.empty:
        st.dataframe(
            co_occurrence.rename(columns={"label_pair": "Label Pair", "count": "Issues Together"}),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No label co-occurrence data available.")
