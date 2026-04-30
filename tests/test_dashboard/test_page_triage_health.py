"""Tests for dashboard/pages/2_Triage_Health.py."""
from __future__ import annotations

import pytest

from tests.test_dashboard._page_test_utils import (
    PageStopped,
    metric_labels,
    metric_value_for,
    run_page,
)

PAGE = "2_Triage_Health.py"


class TestTriageHealthPageGuards:
    def test_warns_and_stops_when_no_data_loaded(self, streamlit_mock):
        with pytest.raises(PageStopped):
            run_page(PAGE, streamlit_mock)
        streamlit_mock.warning.assert_called_once()
        streamlit_mock.stop.assert_called_once()
        streamlit_mock.plotly_chart.assert_not_called()


class TestTriageHealthPageRendering:
    def test_renders_header_and_three_kpis(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        streamlit_mock.header.assert_called_with("Triage Health")
        assert metric_labels(streamlit_mock) == [
            "Median First Response",
            "Median Time to Label",
            "Unlabeled Issues",
        ]

    def test_kpi_values_match_triage_metrics(
        self, streamlit_mock, sample_issues, sample_events
    ):
        from metrics import triage_metrics  # type: ignore[import-not-found]

        expected = triage_metrics(sample_issues, sample_events)
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        assert (
            metric_value_for(streamlit_mock, "Median First Response")
            == f"{expected['median_first_response_days']} days"
        )
        assert (
            metric_value_for(streamlit_mock, "Median Time to Label")
            == f"{expected['median_time_to_label_days']} days"
        )
        assert metric_value_for(streamlit_mock, "Unlabeled Issues") == f"{expected['unlabeled_count']:,}"

    def test_renders_histogram_and_monthly_trend_when_data_present(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        # Two charts: response time histogram + monthly median trend.
        assert streamlit_mock.plotly_chart.call_count == 2
        streamlit_mock.info.assert_not_called()

    def test_shows_info_when_no_response_time_data(
        self, streamlit_mock, no_response_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = no_response_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        # Both branches should fall through to the info message instead of charts.
        assert streamlit_mock.plotly_chart.call_count == 0
        assert streamlit_mock.info.call_count == 2

    def test_unlabeled_count_reflects_empty_label_lists(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        # Issue #3 is the only one with empty labels.
        assert metric_value_for(streamlit_mock, "Unlabeled Issues") == "1"

    def test_na_metrics_when_response_data_missing(
        self, streamlit_mock, no_response_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = no_response_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        assert metric_value_for(streamlit_mock, "Median First Response") == "N/A"
        assert metric_value_for(streamlit_mock, "Median Time to Label") == "N/A"
