import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone


def build_issues_dataframe(raw_data: list[dict]) -> pd.DataFrame:
    """Convert raw JSON list into issues DataFrame."""
    rows = []
    for issue in raw_data:
        labels = issue.get("labels", [])
        labels_lower = [l.lower() for l in labels]
        rows.append({
            "number": issue["number"],
            "creator": issue.get("creator", ""),
            "state": issue.get("state", "open"),
            "labels": labels,
            "assignees": issue.get("assignees", []),
            "title": issue.get("title", ""),
            "text": issue.get("text", ""),
            "url": issue.get("url", ""),
            "created_date": pd.to_datetime(issue.get("created_date"), utc=True, errors="coerce"),
            "updated_date": pd.to_datetime(issue.get("updated_date"), utc=True, errors="coerce"),
            "event_count": len(issue.get("events", [])),
            "is_bug": any("bug" in l for l in labels_lower),
            "is_feature": any("feature" in l for l in labels_lower),
        })
    df = pd.DataFrame(rows)
    return df


def build_events_dataframe(raw_data: list[dict]) -> pd.DataFrame:
    """Flatten all events across all issues into one DataFrame."""
    rows = []
    for issue in raw_data:
        for event in issue.get("events", []):
            rows.append({
                "issue_number": issue["number"],
                "event_type": event.get("event_type", ""),
                "author": event.get("author", ""),
                "event_date": pd.to_datetime(event.get("event_date"), utc=True, errors="coerce"),
                "label": event.get("label", ""),
                "comment": event.get("comment", ""),
            })
    if not rows:
        return pd.DataFrame(columns=["issue_number", "event_type", "author", "event_date", "label", "comment"])
    return pd.DataFrame(rows)


def add_computed_columns(df_issues: pd.DataFrame, df_events: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns to the issues DataFrame."""
    now = pd.Timestamp.now(tz="UTC")

    df_issues["days_to_close"] = np.where(
        df_issues["state"] == "closed",
        (df_issues["updated_date"] - df_issues["created_date"]).dt.total_seconds() / 86400,
        np.nan,
    )

    if not df_events.empty:
        first_event = df_events.groupby("issue_number")["event_date"].min().rename("first_event_date")
        df_issues = df_issues.merge(first_event, left_on="number", right_index=True, how="left")
        df_issues["time_to_first_response"] = (
            (df_issues["first_event_date"] - df_issues["created_date"]).dt.total_seconds() / 86400
        )
        df_issues.drop(columns=["first_event_date"], inplace=True)

        label_events = df_events[df_events["event_type"] == "LabeledEvent"]
        if not label_events.empty:
            first_label = label_events.groupby("issue_number")["event_date"].min().rename("first_label_date")
            df_issues = df_issues.merge(first_label, left_on="number", right_index=True, how="left")
            df_issues["time_to_first_label"] = (
                (df_issues["first_label_date"] - df_issues["created_date"]).dt.total_seconds() / 86400
            )
            df_issues.drop(columns=["first_label_date"], inplace=True)
        else:
            df_issues["time_to_first_label"] = np.nan

        last_event = df_events.groupby("issue_number")["event_date"].max().rename("last_event_date")
        df_issues = df_issues.merge(last_event, left_on="number", right_index=True, how="left")
        df_issues["last_activity"] = df_issues[["updated_date", "last_event_date"]].max(axis=1)
        df_issues.drop(columns=["last_event_date"], inplace=True)
    else:
        df_issues["time_to_first_response"] = np.nan
        df_issues["time_to_first_label"] = np.nan
        df_issues["last_activity"] = df_issues["updated_date"]

    df_issues["days_since_last_activity"] = (
        (now - df_issues["last_activity"]).dt.total_seconds() / 86400
    )

    conditions = [
        df_issues["days_since_last_activity"] < 30,
        df_issues["days_since_last_activity"] < 90,
        df_issues["days_since_last_activity"] < 365,
        df_issues["days_since_last_activity"] >= 365,
    ]
    choices = ["Active", "Aging", "Stale", "Zombie"]
    df_issues["staleness_bucket"] = np.select(conditions, choices, default="Active")

    return df_issues


def load_data(json_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load Poetry.json and return (df_issues, df_events) with computed columns."""
    with open(json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    df_issues = build_issues_dataframe(raw_data)
    df_events = build_events_dataframe(raw_data)
    df_issues = add_computed_columns(df_issues, df_events)
    return df_issues, df_events
