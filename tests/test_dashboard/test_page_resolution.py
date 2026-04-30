"""Tests for dashboard/pages/6_Resolution.py."""
from __future__ import annotations

import pytest

from tests.test_dashboard._page_test_utils import (
    PageStopped,
    metric_labels,
    metric_value_for,
    run_page,
)

PAGE = "6_Resolution.py"


class TestResolutionPageGuards:
    def test_warns_and_stops_when_no_data_loaded(self, streamlit_mock):
        with pytest.raises(PageStopped):
            run_page(PAGE, streamlit_mock)
        streamlit_mock.warning.assert_called_once()
        streamlit_mock.stop.assert_called_once()
        streamlit_mock.plotly_chart.assert_not_called()


class TestResolutionPageRendering:
    def test_renders_header_and_four_kpis(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        streamlit_mock.header.assert_called_with("Resolution Efficiency")
        assert metric_labels(streamlit_mock) == [
            "Median Days to Close",
            "Reopen Rate",
            "Closed This Month",
            "Net Open (This Month)",
        ]

    def test_kpi_values_match_resolution_metrics(
        self, streamlit_mock, sample_issues, sample_events
    ):
        from metrics import resolution_metrics  # type: ignore[import-not-found]

        expected = resolution_metrics(sample_issues, sample_events)
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        assert metric_value_for(streamlit_mock, "Median Days to Close") == f"{expected['median_days_to_close']}"
        assert metric_value_for(streamlit_mock, "Reopen Rate") == f"{expected['reopen_rate']}%"
        assert metric_value_for(streamlit_mock, "Closed This Month") == f"{expected['closed_this_month']:,}"
        assert metric_value_for(streamlit_mock, "Net Open (This Month)") == f"{expected['net_open_this_month']:+,}"

    def test_renders_histogram_and_monthly_chart(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        # Time-to-close histogram + monthly created/closed line chart.
        assert streamlit_mock.plotly_chart.call_count == 2

    def test_median_close_na_when_no_closed_issues(
        self, streamlit_mock, open_only_issues, empty_events
    ):
        streamlit_mock.session_state["df_issues"] = open_only_issues
        streamlit_mock.session_state["df_events"] = empty_events

        run_page(PAGE, streamlit_mock)

        assert metric_value_for(streamlit_mock, "Median Days to Close") == "N/A"
        # No closed issues -> no histogram.
        assert streamlit_mock.plotly_chart.call_count == 1  # only monthly chart

    def test_most_reopened_table_rendered_when_reopens_exist(
        self, streamlit_mock, sample_issues, reopen_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = reopen_events

        run_page(PAGE, streamlit_mock)

        assert streamlit_mock.dataframe.called
        df_arg = streamlit_mock.dataframe.call_args.args[0]
        assert list(df_arg.columns) == ["#", "Title", "Reopens", "Labels", "State"]
        assert 1 in df_arg["#"].tolist()
        streamlit_mock.info.assert_not_called()

    def test_info_shown_when_no_reopened_issues(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        streamlit_mock.info.assert_called_once()
        assert "No reopened issues" in streamlit_mock.info.call_args.args[0]

    def test_reopen_rate_reflects_event_count(
        self, streamlit_mock, sample_issues, reopen_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = reopen_events

        run_page(PAGE, streamlit_mock)

        # 1 reopened issue out of 3 total -> 33.3%
        assert metric_value_for(streamlit_mock, "Reopen Rate") == "33.3%"
