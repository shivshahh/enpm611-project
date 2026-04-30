"""Shared fixtures for dashboard page tests."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tests.test_dashboard._page_test_utils import make_streamlit_mock


@pytest.fixture
def streamlit_mock():
    """Fresh mocked streamlit module with a per-test session_state dict."""
    return make_streamlit_mock()


def _now() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC")


@pytest.fixture
def sample_issues() -> pd.DataFrame:
    """Three issues spanning closed/open, labeled/unlabeled, recent/older."""
    now = _now()
    rows = [
        {
            "number": 1,
            "creator": "alice",
            "state": "closed",
            "labels": ["bug"],
            "assignees": [],
            "title": "old bug",
            "text": "",
            "url": "https://example/1",
            "created_date": now - pd.Timedelta(days=200),
            "updated_date": now - pd.Timedelta(days=100),
            "event_count": 2,
            "is_bug": True,
            "is_feature": False,
            "days_to_close": 100.0,
            "time_to_first_response": 0.5,
            "time_to_first_label": 1.0,
            "last_activity": now - pd.Timedelta(days=100),
            "days_since_last_activity": 100.0,
            "staleness_bucket": "Aging",
        },
        {
            "number": 2,
            "creator": "bob",
            "state": "open",
            "labels": ["feature"],
            "assignees": [],
            "title": "recent feature",
            "text": "",
            "url": "https://example/2",
            "created_date": now - pd.Timedelta(days=30),
            "updated_date": now - pd.Timedelta(days=10),
            "event_count": 1,
            "is_bug": False,
            "is_feature": True,
            "days_to_close": np.nan,
            "time_to_first_response": 2.0,
            "time_to_first_label": 3.0,
            "last_activity": now - pd.Timedelta(days=10),
            "days_since_last_activity": 10.0,
            "staleness_bucket": "Active",
        },
        {
            "number": 3,
            "creator": "alice",
            "state": "open",
            "labels": [],
            "assignees": [],
            "title": "fresh unlabeled",
            "text": "",
            "url": "https://example/3",
            "created_date": now - pd.Timedelta(days=5),
            "updated_date": now - pd.Timedelta(days=1),
            "event_count": 0,
            "is_bug": False,
            "is_feature": False,
            "days_to_close": np.nan,
            "time_to_first_response": np.nan,
            "time_to_first_label": np.nan,
            "last_activity": now - pd.Timedelta(days=1),
            "days_since_last_activity": 1.0,
            "staleness_bucket": "Active",
        },
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def sample_events() -> pd.DataFrame:
    """Events covering comments and a labeling event."""
    now = _now()
    rows = [
        {
            "issue_number": 1,
            "event_type": "commented",
            "author": "carol",
            "event_date": now - pd.Timedelta(days=199),
            "label": "",
            "comment": "first reply",
        },
        {
            "issue_number": 1,
            "event_type": "LabeledEvent",
            "author": "carol",
            "event_date": now - pd.Timedelta(days=199),
            "label": "bug",
            "comment": "",
        },
        {
            "issue_number": 2,
            "event_type": "commented",
            "author": "carol",
            "event_date": now - pd.Timedelta(days=28),
            "label": "",
            "comment": "thanks!",
        },
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def empty_events() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["issue_number", "event_type", "author", "event_date", "label", "comment"]
    )


@pytest.fixture
def open_only_issues(sample_issues) -> pd.DataFrame:
    """Issues with no closed rows (so days_to_close is all NaN)."""
    df = sample_issues.copy()
    df["state"] = "open"
    df["days_to_close"] = np.nan
    return df


@pytest.fixture
def no_response_issues(sample_issues) -> pd.DataFrame:
    """Issues with no first-response data (NaN across the board)."""
    df = sample_issues.copy()
    df["time_to_first_response"] = np.nan
    df["time_to_first_label"] = np.nan
    return df


@pytest.fixture
def staleness_issues() -> pd.DataFrame:
    """Open issues spanning every staleness bucket (Active/Aging/Stale/Zombie)."""
    now = _now()

    def _row(num, days_idle, bucket, labels, event_count):
        last = now - pd.Timedelta(days=days_idle)
        return {
            "number": num,
            "creator": f"user{num}",
            "state": "open",
            "labels": labels,
            "assignees": [],
            "title": f"issue {num}",
            "text": "",
            "url": f"https://example/{num}",
            "created_date": last - pd.Timedelta(days=10),
            "updated_date": last,
            "event_count": event_count,
            "is_bug": "bug" in labels,
            "is_feature": "feature" in labels,
            "days_to_close": np.nan,
            "time_to_first_response": np.nan if event_count == 0 else 1.0,
            "time_to_first_label": np.nan,
            "last_activity": last,
            "days_since_last_activity": float(days_idle),
            "staleness_bucket": bucket,
        }

    return pd.DataFrame([
        _row(101, 5, "Active", ["bug"], 2),
        _row(102, 60, "Aging", ["feature"], 1),
        _row(103, 200, "Stale", ["bug"], 0),
        _row(104, 500, "Zombie", [], 0),
    ])


@pytest.fixture
def reopen_events(sample_events) -> pd.DataFrame:
    """sample_events extended with a ReopenedEvent on issue #1."""
    now = _now()
    extra = pd.DataFrame([{
        "issue_number": 1,
        "event_type": "ReopenedEvent",
        "author": "carol",
        "event_date": now - pd.Timedelta(days=50),
        "label": "",
        "comment": "",
    }])
    return pd.concat([sample_events, extra], ignore_index=True)


@pytest.fixture
def multi_label_issues(sample_issues) -> pd.DataFrame:
    """Issues that share label pairs, so co-occurrence analysis has data."""
    df = sample_issues.copy()
    df.at[0, "labels"] = ["bug", "regression"]
    df.at[1, "labels"] = ["feature", "ux"]
    df.at[2, "labels"] = ["bug", "regression"]
    df["is_bug"] = df["labels"].apply(lambda ls: any("bug" in l for l in ls))
    df["is_feature"] = df["labels"].apply(lambda ls: any("feature" in l for l in ls))
    return df
