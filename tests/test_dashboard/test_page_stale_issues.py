"""Tests for dashboard/pages/5_Stale_Issues.py."""
from __future__ import annotations

import pytest

from tests.test_dashboard._page_test_utils import (
    PageStopped,
    metric_labels,
    metric_value_for,
    run_page,
)

PAGE = "5_Stale_Issues.py"


class TestStalePageGuards:
    def test_warns_and_stops_when_no_data_loaded(self, streamlit_mock):
        with pytest.raises(PageStopped):
            run_page(PAGE, streamlit_mock)
        streamlit_mock.warning.assert_called_once()
        streamlit_mock.stop.assert_called_once()
        streamlit_mock.plotly_chart.assert_not_called()


class TestStalePageRendering:
    def test_renders_header_and_three_kpis(self, streamlit_mock, staleness_issues):
        streamlit_mock.session_state["df_issues"] = staleness_issues

        run_page(PAGE, streamlit_mock)

        streamlit_mock.header.assert_called_with("Stale Issues")
        assert metric_labels(streamlit_mock) == [
            "Stale Issues (>90d idle)",
            "Zombie Issues (>1yr idle)",
            "No Response Ever",
        ]

    def test_kpi_values_match_staleness_metrics(self, streamlit_mock, staleness_issues):
        from metrics import staleness_metrics  # type: ignore[import-not-found]

        expected = staleness_metrics(staleness_issues)
        streamlit_mock.session_state["df_issues"] = staleness_issues

        run_page(PAGE, streamlit_mock)

        assert metric_value_for(streamlit_mock, "Stale Issues (>90d idle)") == f"{expected['stale_count']:,}"
        assert metric_value_for(streamlit_mock, "Zombie Issues (>1yr idle)") == f"{expected['zombie_count']:,}"
        assert metric_value_for(streamlit_mock, "No Response Ever") == f"{expected['no_response_count']:,}"

    def test_renders_distribution_bar_when_buckets_have_data(
        self, streamlit_mock, staleness_issues
    ):
        streamlit_mock.session_state["df_issues"] = staleness_issues

        run_page(PAGE, streamlit_mock)

        # One stacked-bar chart for the bucket distribution.
        assert streamlit_mock.plotly_chart.call_count == 1

    def test_attention_dataframe_lists_stale_and_zombie_issues(
        self, streamlit_mock, staleness_issues
    ):
        streamlit_mock.session_state["df_issues"] = staleness_issues

        run_page(PAGE, streamlit_mock)

        assert streamlit_mock.dataframe.called
        df_arg = streamlit_mock.dataframe.call_args.args[0]
        assert list(df_arg.columns) == [
            "#", "Title", "Labels", "Last Activity", "Days Idle", "Status",
        ]
        # Issues #103 (Stale) and #104 (Zombie) should appear.
        assert set(df_arg["#"]) == {103, 104}

    def test_success_shown_when_no_stale_issues(self, streamlit_mock, sample_issues):
        # sample_issues only has Active issues, so attention list is empty.
        streamlit_mock.session_state["df_issues"] = sample_issues

        run_page(PAGE, streamlit_mock)

        streamlit_mock.success.assert_called_once()
        assert "No stale issues" in streamlit_mock.success.call_args.args[0]
        streamlit_mock.dataframe.assert_not_called()

    def test_no_chart_when_no_open_issues(self, streamlit_mock, sample_issues):
        df = sample_issues.copy()
        df["state"] = "closed"
        streamlit_mock.session_state["df_issues"] = df

        run_page(PAGE, streamlit_mock)

        # No open issues -> total == 0 -> bar chart is skipped.
        streamlit_mock.plotly_chart.assert_not_called()
