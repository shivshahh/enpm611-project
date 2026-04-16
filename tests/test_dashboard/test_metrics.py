import pytest
import pandas as pd
import numpy as np

SAMPLE_DATA = [
    {
        "url": "https://github.com/python-poetry/poetry/issues/1",
        "creator": "alice", "labels": ["kind/bug", "area/install"], "state": "closed",
        "assignees": ["bob"], "title": "Bug in install", "text": "Install fails",
        "number": 1, "created_date": "2024-01-01T00:00:00Z", "updated_date": "2024-01-10T00:00:00Z",
        "timeline_url": "", "events": [
            {"event_type": "commented", "author": "bob", "event_date": "2024-01-02T00:00:00Z", "comment": "Looking into it"},
            {"event_type": "LabeledEvent", "author": "bob", "event_date": "2024-01-03T00:00:00Z", "comment": ""},
            {"event_type": "ClosedEvent", "author": "bob", "event_date": "2024-01-10T00:00:00Z", "comment": ""},
        ],
    },
    {
        "url": "https://github.com/python-poetry/poetry/issues/2",
        "creator": "charlie", "labels": ["kind/feature"], "state": "open",
        "assignees": [], "title": "Add new feature", "text": "Please add X",
        "number": 2, "created_date": "2024-06-01T00:00:00Z", "updated_date": "2024-06-01T00:00:00Z",
        "timeline_url": "", "events": [],
    },
    {
        "url": "https://github.com/python-poetry/poetry/issues/3",
        "creator": "alice", "labels": ["kind/bug"], "state": "closed",
        "assignees": [], "title": "Another bug", "text": "Crash on startup",
        "number": 3, "created_date": "2024-03-01T00:00:00Z", "updated_date": "2024-03-05T00:00:00Z",
        "timeline_url": "", "events": [
            {"event_type": "commented", "author": "alice", "event_date": "2024-03-02T00:00:00Z", "comment": "Workaround found"},
            {"event_type": "ClosedEvent", "author": "alice", "event_date": "2024-03-05T00:00:00Z", "comment": ""},
            {"event_type": "ReopenedEvent", "author": "bob", "event_date": "2024-03-06T00:00:00Z", "comment": ""},
            {"event_type": "ClosedEvent", "author": "bob", "event_date": "2024-03-08T00:00:00Z", "comment": ""},
        ],
    },
]


@pytest.fixture
def dataframes():
    from dashboard.data_loader import build_issues_dataframe, build_events_dataframe, add_computed_columns
    df_issues = build_issues_dataframe(SAMPLE_DATA)
    df_events = build_events_dataframe(SAMPLE_DATA)
    df_issues = add_computed_columns(df_issues, df_events)
    return df_issues, df_events


def test_triage_metrics(dataframes):
    from dashboard.metrics import triage_metrics
    df_issues, df_events = dataframes
    result = triage_metrics(df_issues, df_events)
    assert "median_first_response_days" in result
    assert "median_time_to_label_days" in result
    assert "unlabeled_count" in result
    assert result["unlabeled_count"] == 0


def test_contributor_metrics(dataframes):
    from dashboard.metrics import contributor_metrics
    df_issues, df_events = dataframes
    result = contributor_metrics(df_issues, df_events)
    assert result["total_contributors"] >= 3
    assert "top_contributors" in result
    assert isinstance(result["top_contributors"], pd.DataFrame)


def test_resolution_metrics(dataframes):
    from dashboard.metrics import resolution_metrics
    df_issues, df_events = dataframes
    result = resolution_metrics(df_issues, df_events)
    assert "median_days_to_close" in result
    assert "reopen_rate" in result
    assert result["reopen_rate"] > 0
    assert "most_reopened" in result


def test_label_metrics(dataframes):
    from dashboard.metrics import label_metrics
    df_issues, df_events = dataframes
    result = label_metrics(df_issues)
    assert result["unique_labels"] == 3
    assert result["unlabeled_count"] == 0
    assert "label_counts" in result
    assert isinstance(result["label_counts"], pd.DataFrame)
    assert "co_occurrence" in result
