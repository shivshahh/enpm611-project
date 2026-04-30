"""Tests for dashboard/pages/3_Contributors.py."""
from __future__ import annotations

import pytest

from tests.test_dashboard._page_test_utils import (
    PageStopped,
    metric_labels,
    metric_value_for,
    run_page,
)

PAGE = "3_Contributors.py"


class TestContributorsPageGuards:
    def test_warns_and_stops_when_no_data_loaded(self, streamlit_mock):
        with pytest.raises(PageStopped):
            run_page(PAGE, streamlit_mock)
        streamlit_mock.warning.assert_called_once()
        streamlit_mock.stop.assert_called_once()


class TestContributorsPageRendering:
    def test_renders_header_and_four_kpis(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        streamlit_mock.header.assert_called_with("Contributors")
        assert metric_labels(streamlit_mock) == [
            "Total Contributors",
            "Active (90d)",
            "New This Month",
            "Returning",
        ]

    def test_kpi_values_match_contributor_metrics(
        self, streamlit_mock, sample_issues, sample_events
    ):
        from metrics import contributor_metrics  # type: ignore[import-not-found]

        expected = contributor_metrics(sample_issues, sample_events)
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        assert metric_value_for(streamlit_mock, "Total Contributors") == f"{expected['total_contributors']:,}"
        assert metric_value_for(streamlit_mock, "Active (90d)") == f"{expected['active_90d']:,}"
        assert metric_value_for(streamlit_mock, "New This Month") == f"{expected['new_this_month']:,}"
        assert metric_value_for(streamlit_mock, "Returning") == f"{expected['returning']:,}"

    def test_renders_top_contributors_dataframe_and_charts(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        # The dataframe widget is shown for the top contributors table.
        assert streamlit_mock.dataframe.called
        # Two plotly charts when events are present: monthly bar + heatmap.
        assert streamlit_mock.plotly_chart.call_count == 2
        streamlit_mock.info.assert_not_called()

    def test_top_contributors_table_includes_known_authors(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        # Inspect the DataFrame passed to st.dataframe for the top-contributors table.
        df_arg = streamlit_mock.dataframe.call_args.args[0]
        users = set(df_arg["user"].tolist())
        assert {"alice", "bob", "carol"}.issubset(users)

    def test_skips_heatmap_and_warns_when_events_empty(
        self, streamlit_mock, sample_issues, empty_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = empty_events

        run_page(PAGE, streamlit_mock)

        # Monthly bar still renders (uses df_issues fallback) but heatmap is skipped.
        assert streamlit_mock.plotly_chart.call_count == 1
        streamlit_mock.info.assert_called_once()
        msg = streamlit_mock.info.call_args.args[0]
        assert "No event data" in msg

    def test_total_contributors_includes_event_authors(
        self, streamlit_mock, sample_issues, sample_events
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues
        streamlit_mock.session_state["df_events"] = sample_events

        run_page(PAGE, streamlit_mock)

        # alice + bob (creators) + carol (event author) = 3
        assert metric_value_for(streamlit_mock, "Total Contributors") == "3"
