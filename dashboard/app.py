import streamlit as st
import os

st.set_page_config(
    page_title="Poetry Issues Dashboard",
    page_icon="📊",
    layout="wide",
)

from data_loader import load_data
from filters import render_sidebar, apply_filters


@st.cache_data
def get_data():
    json_path = os.path.join(os.path.dirname(__file__), "..", "Poetry.json")
    json_path = os.path.abspath(json_path)
    return load_data(json_path)


df_issues, df_events = get_data()

filters = render_sidebar(df_issues)
filtered_issues = apply_filters(df_issues, filters)

st.session_state["df_issues"] = filtered_issues
st.session_state["df_events"] = df_events
st.session_state["df_issues_unfiltered"] = df_issues

st.title("📊 Poetry Issues Dashboard")
st.markdown(
    "Actionable insights from the "
    "[python-poetry/poetry](https://github.com/python-poetry/poetry) GitHub project. "
    f"Showing **{len(filtered_issues):,}** of **{len(df_issues):,}** issues."
)
st.markdown("👈 Use the sidebar to filter data, then navigate to a page.")
