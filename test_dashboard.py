import unittest

from _page_test_utils import (
    PageStopped,
    metric_labels,
    metric_value_for,
    run_page,
    make_streamlit_mock,
)

# ChatGPT assisted in the conversion of original tests written for pytest to be compatible with unittest

# =========================================================
# BASE CLASS (shared fixtures)
# =========================================================

class BaseDashboardTest(unittest.TestCase):

    def setUp(self):
        self.st = make_streamlit_mock()

    # ---------------------------
    # DATA FIXTURES
    # ---------------------------
    def make_sample_issues(self):
        import pandas as pd
        import numpy as np

        now = pd.Timestamp.now(tz="UTC")

        return pd.DataFrame([
            {
                "number": 1,
                "creator": "alice",
                "state": "closed",
                "labels": ["bug"],
                "assignees": [],
                "title": "old bug",
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
                "url": "https://example/2",
                "created_date": now - pd.Timedelta(days=30),
                "updated_date": now - pd.Timedelta(days=10),
                "event_count": 1,
                "is_bug": False,
                "is_feature": True,
                "days_to_close": None,
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
                "url": "https://example/3",
                "created_date": now - pd.Timedelta(days=5),
                "updated_date": now - pd.Timedelta(days=1),
                "event_count": 0,
                "is_bug": False,
                "is_feature": False,
                "days_to_close": None,
                "time_to_first_response": None,
                "time_to_first_label": None,
                "last_activity": now - pd.Timedelta(days=1),
                "days_since_last_activity": 1.0,
                "staleness_bucket": "Active",
            },
        ])

    def make_sample_events(self):
        import pandas as pd
        now = pd.Timestamp.now(tz="UTC")

        return pd.DataFrame([
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
        ])

    def make_empty_events(self):
        import pandas as pd
        return pd.DataFrame(columns=["issue_number", "event_type", "author", "event_date", "label", "comment"])

    def make_open_only_issues(self):
        df = self.make_sample_issues().copy()
        df["state"] = "open"
        df["days_to_close"] = None
        return df

    def make_no_response_issues(self):
        df = self.make_sample_issues().copy()
        df["time_to_first_response"] = None
        df["time_to_first_label"] = None
        return df

    def make_multi_label_issues(self):
        df = self.make_sample_issues().copy()
        df.at[0, "labels"] = ["bug", "regression"]
        df.at[1, "labels"] = ["feature", "ux"]
        df.at[2, "labels"] = ["bug", "regression"]
        return df


# =========================================================
# OVERVIEW PAGE
# =========================================================

class TestOverviewPage(BaseDashboardTest):

    def test_no_data(self):
        with self.assertRaises(PageStopped):
            run_page("1_Overview.py", self.st)

        self.st.warning.assert_called_once()
        self.st.stop.assert_called_once()
        self.st.plotly_chart.assert_not_called()
        self.assertEqual(metric_labels(self.st), [])

    def test_rendering(self):
        self.st.session_state["df_issues"] = self.make_sample_issues()
        self.st.session_state["df_events"] = self.make_sample_events()

        run_page("1_Overview.py", self.st)

        self.st.header.assert_called_with("Overview")

        self.assertEqual(metric_labels(self.st), [
            "Total Issues",
            "Open Issues",
            "Avg Days to Close",
            "Active Contributors (90d)",
        ])

        self.assertEqual(metric_value_for(self.st, "Total Issues"), "3")
        self.assertEqual(metric_value_for(self.st, "Open Issues"), "2")
        self.assertEqual(metric_value_for(self.st, "Avg Days to Close"), "100.0")

    def test_active_contributors(self):
        self.st.session_state["df_issues"] = self.make_sample_issues()
        self.st.session_state["df_events"] = self.make_sample_events()

        run_page("1_Overview.py", self.st)

        self.assertEqual(metric_value_for(self.st, "Active Contributors (90d)"), "3")

    def test_avg_na(self):
        self.st.session_state["df_issues"] = self.make_open_only_issues()
        self.st.session_state["df_events"] = self.make_sample_events()

        run_page("1_Overview.py", self.st)

        self.assertEqual(metric_value_for(self.st, "Avg Days to Close"), "N/A")

    def test_charts(self):
        self.st.session_state["df_issues"] = self.make_sample_issues()
        self.st.session_state["df_events"] = self.make_sample_events()

        run_page("1_Overview.py", self.st)

        self.assertEqual(self.st.plotly_chart.call_count, 2)

    def test_empty_events(self):
        self.st.session_state["df_issues"] = self.make_sample_issues()
        self.st.session_state["df_events"] = self.make_empty_events()

        run_page("1_Overview.py", self.st)

        self.assertEqual(metric_value_for(self.st, "Active Contributors (90d)"), "2")

    def test_open_rate_delta(self):
        self.st.session_state["df_issues"] = self.make_sample_issues()
        self.st.session_state["df_events"] = self.make_sample_events()

        run_page("1_Overview.py", self.st)

        found = False
        for col in self.st._columns_created:
            for call in col.metric.call_args_list:
                if call.args and call.args[0] == "Open Issues":
                    if len(call.args) >= 3:
                        self.assertEqual(call.args[2], "66.7% open rate")
                        found = True
        self.assertTrue(found)


# =========================================================
# TRIAGE HEALTH
# =========================================================

class TestTriageHealthPage(BaseDashboardTest):

    def test_no_data(self):
        with self.assertRaises(PageStopped):
            run_page("2_Triage_Health.py", self.st)

    def test_kpis(self):
        from dashboard.metrics import triage_metrics

        issues = self.make_sample_issues()
        events = self.make_sample_events()

        expected = triage_metrics(issues, events)

        self.st.session_state["df_issues"] = issues
        self.st.session_state["df_events"] = events

        run_page("2_Triage_Health.py", self.st)

        self.assertEqual(
            metric_value_for(self.st, "Unlabeled Issues"),
            f"{expected['unlabeled_count']:,}"
        )


# =========================================================
# TRENDS
# =========================================================

class TestTrendsPage(BaseDashboardTest):

    def test_kpis(self):
        from dashboard.metrics import trend_metrics

        issues = self.make_sample_issues()
        expected = trend_metrics(issues)

        self.st.session_state["df_issues"] = issues

        run_page("4_Trends.py", self.st)

        self.assertEqual(
            metric_value_for(self.st, "Bug Issues"),
            f"{expected['bug_count']:,}"
        )


# =========================================================
# STALE
# =========================================================

class TestStalePage(BaseDashboardTest):

    def test_no_data(self):
        with self.assertRaises(PageStopped):
            run_page("5_Stale_Issues.py", self.st)


# =========================================================
# RESOLUTION
# =========================================================

class TestResolutionPage(BaseDashboardTest):

    def test_kpis(self):
        from dashboard.metrics import resolution_metrics

        issues = self.make_sample_issues()
        events = self.make_sample_events()

        expected = resolution_metrics(issues, events)

        self.st.session_state["df_issues"] = issues
        self.st.session_state["df_events"] = events

        run_page("6_Resolution.py", self.st)

        self.assertEqual(
            metric_value_for(self.st, "Closed This Month"),
            f"{expected['closed_this_month']:,}"
        )


# =========================================================
# CONTRIBUTORS
# =========================================================

class TestContributorsPage(BaseDashboardTest):

    def test_no_data(self):
        with self.assertRaises(PageStopped):
            run_page("3_Contributors.py", self.st)

    def test_total_contributors(self):
        self.st.session_state["df_issues"] = self.make_sample_issues()
        self.st.session_state["df_events"] = self.make_sample_events()

        run_page("3_Contributors.py", self.st)

        self.assertEqual(
            metric_value_for(self.st, "Total Contributors"),
            "3"
        )


# =========================================================
# LABELS
# =========================================================

class TestLabelsPage(BaseDashboardTest):

    def test_kpis(self):
        from dashboard.metrics import label_metrics

        issues = self.make_sample_issues()
        expected = label_metrics(issues)

        self.st.session_state["df_issues"] = issues

        run_page("7_Labels.py", self.st)

        self.assertEqual(
            metric_value_for(self.st, "Unique Labels"),
            f"{expected['unique_labels']:,}"
        )


# =========================================================

if __name__ == "__main__":
    unittest.main()