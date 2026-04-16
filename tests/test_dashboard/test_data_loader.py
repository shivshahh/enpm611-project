import pytest
import pandas as pd
from datetime import datetime

SAMPLE_DATA = [
    {
        "url": "https://github.com/python-poetry/poetry/issues/1",
        "creator": "alice",
        "labels": ["kind/bug", "area/install"],
        "state": "closed",
        "assignees": ["bob"],
        "title": "Bug in install",
        "text": "Install fails",
        "number": 1,
        "created_date": "2024-01-01T00:00:00Z",
        "updated_date": "2024-01-10T00:00:00Z",
        "timeline_url": "https://api.github.com/repos/python-poetry/poetry/issues/1/timeline",
        "events": [
            {"event_type": "commented", "author": "bob", "event_date": "2024-01-02T00:00:00Z", "comment": "Looking into it"},
            {"event_type": "LabeledEvent", "author": "bob", "event_date": "2024-01-03T00:00:00Z", "comment": "", "label": "kind/bug"},
            {"event_type": "ClosedEvent", "author": "bob", "event_date": "2024-01-10T00:00:00Z", "comment": ""},
        ],
    },
    {
        "url": "https://github.com/python-poetry/poetry/issues/2",
        "creator": "charlie",
        "labels": ["kind/feature"],
        "state": "open",
        "assignees": [],
        "title": "Add new feature",
        "text": "Please add X",
        "number": 2,
        "created_date": "2024-06-01T00:00:00Z",
        "updated_date": "2024-06-01T00:00:00Z",
        "timeline_url": "https://api.github.com/repos/python-poetry/poetry/issues/2/timeline",
        "events": [],
    },
]


def test_build_issues_dataframe():
    from dashboard.data_loader import build_issues_dataframe
    df = build_issues_dataframe(SAMPLE_DATA)
    assert len(df) == 2
    row1 = df[df["number"] == 1].iloc[0]
    assert row1["is_bug"] == True
    assert row1["is_feature"] == False
    assert row1["state"] == "closed"
    assert row1["event_count"] == 3
    row2 = df[df["number"] == 2].iloc[0]
    assert row2["is_bug"] == False
    assert row2["is_feature"] == True
    assert row2["event_count"] == 0


def test_build_events_dataframe():
    from dashboard.data_loader import build_events_dataframe
    df = build_events_dataframe(SAMPLE_DATA)
    assert len(df) == 3
    assert set(df.columns) >= {"issue_number", "event_type", "author", "event_date"}
    assert df[df["issue_number"] == 1].shape[0] == 3
    assert df[df["issue_number"] == 2].shape[0] == 0


def test_computed_columns():
    from dashboard.data_loader import build_issues_dataframe, build_events_dataframe, add_computed_columns
    df_issues = build_issues_dataframe(SAMPLE_DATA)
    df_events = build_events_dataframe(SAMPLE_DATA)
    df_issues = add_computed_columns(df_issues, df_events)
    row1 = df_issues[df_issues["number"] == 1].iloc[0]
    assert row1["days_to_close"] == 9.0
    assert row1["time_to_first_response"] == 1.0
    assert row1["time_to_first_label"] == 2.0
    row2 = df_issues[df_issues["number"] == 2].iloc[0]
    assert pd.isna(row2["days_to_close"])
    assert pd.isna(row2["time_to_first_response"])
