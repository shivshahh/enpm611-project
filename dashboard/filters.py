import streamlit as st
import pandas as pd
from datetime import date


def render_sidebar(df_issues: pd.DataFrame) -> dict:
    """Render sidebar filters and return filter settings as a dict."""
    st.sidebar.header("Filters")

    min_date = df_issues["created_date"].min().date()
    max_date = df_issues["created_date"].max().date()
    # Streamlit's built-in calendar presets ("past week" ... "past 2 years")
    # anchor end-of-range to today, so max_value must reach today to accept them.
    picker_max = max(max_date, date.today())
    date_range = st.sidebar.date_input(
        "Created date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=picker_max,
    )

    state = st.sidebar.selectbox("Issue state", ["all", "open", "closed"], index=0)

    all_labels = sorted(set(label for labels in df_issues["labels"] for label in labels))
    selected_labels = st.sidebar.multiselect("Labels", all_labels)

    contributor = st.sidebar.text_input("Contributor (creator)", "")

    return {
        "date_range": date_range,
        "state": state,
        "labels": selected_labels,
        "contributor": contributor,
    }


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply sidebar filters to an issues DataFrame."""
    filtered = df.copy()

    date_range = filters["date_range"]
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start = pd.Timestamp(date_range[0], tz="UTC")
        end = pd.Timestamp(date_range[1], tz="UTC") + pd.Timedelta(days=1)
        filtered = filtered[(filtered["created_date"] >= start) & (filtered["created_date"] < end)]

    if filters["state"] != "all":
        filtered = filtered[filtered["state"] == filters["state"]]

    if filters["labels"]:
        mask = filtered["labels"].apply(lambda issue_labels: all(l in issue_labels for l in filters["labels"]))
        filtered = filtered[mask]

    if filters["contributor"]:
        filtered = filtered[filtered["creator"].str.contains(filters["contributor"], case=False, na=False)]

    return filtered
