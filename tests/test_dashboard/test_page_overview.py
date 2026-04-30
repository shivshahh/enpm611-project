"""Tests for dashboard/pages/1_Overview.py."""
from __future__ import annotations

import pytest

from tests.test_dashboard._page_test_utils import (
    PageStopped,
    metric_labels,
    metric_value_for,
    run_page,
)

PAGE = "1_Overview.py"


class TestOverviewPageGuards:
    def test_warns_and_stops_when_no_data_loaded(self, streamlit_mock):
        with pytest.raises(PageStopped):
            run_page(PAGE, streamlit_mock)
        streamlit_mock.warning.assert_called_once()
        streamlit_mock.stop.assert_called_once()
        # Should never have rendered metrics or charts.
        streamlit_mock.plotly_chart.assert_not_called()
        assert metric_labels(streamlit_mock) == []


class TestOverviewPageRendering:
    def test_renders_header_and_kpi_metrics(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        streamlit_mock.header.assert_called_with("Overview")
        labels = metric_labels(streamlit_mock)
        assert labels == [
            "Total Issues",
            "Open Issues",
            "Avg Days to Close",
            "Active Contributors (90d)",
        ]
        # Total Issues = 3
        assert metric_value_for(streamlit_mock, "Total Issues") == "3"
        # Open Issues = 2 (issues #2 and #3)
        assert metric_value_for(streamlit_mock, "Open Issues") == "2"
        # Avg days to close: only issue #1 has 100.0 -> "100.0"
        assert metric_value_for(streamlit_mock, "Avg Days to Close") == "100.0"

    def test_active_contributors_combines_creators_and_event_authors(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        # bob (creator within 90d), alice (creator within 90d), carol (event author within 90d)
        assert metric_value_for(streamlit_mock, "Active Contributors (90d)") == "3"

    def test_avg_days_to_close_is_na_when_no_closed_issues(
        self, streamlit_mock, open_only_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = open_only_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        assert metric_value_for(streamlit_mock, "Avg Days to Close") == "N/A"

    def test_renders_two_plotly_charts(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        # Line chart (created vs closed) + donut (open/closed split)
        assert streamlit_mock.plotly_chart.call_count == 2

    def test_works_when_events_dataframe_is_empty(
        self, streamlit_mock, sample_issues, empty_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = empty_events

        run_page(PAGE, streamlit_mock)

        # With empty events, active contributors come only from issue creators (alice, bob).
        assert metric_value_for(streamlit_mock, "Active Contributors (90d)") == "2"
        assert streamlit_mock.plotly_chart.call_count == 2

    def test_open_rate_appears_as_metric_delta(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        # The delta arg is the third positional ("66.7% open rate" for 2/3).
        for call in streamlit_mock.method_calls:
            pass  # exhaust to keep mock state stable
        delta_seen = False
        for col in streamlit_mock._columns_created:
            for call in col.metric.call_args_list:
                if call.args and call.args[0] == "Open Issues" and len(call.args) >= 3:
                    assert call.args[2] == "66.7% open rate"
                    delta_seen = True
        assert delta_seen, "Open Issues metric should include open-rate delta"
