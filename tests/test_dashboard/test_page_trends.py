"""Tests for dashboard/pages/4_Trends.py."""
from __future__ import annotations

import pytest

from tests.test_dashboard._page_test_utils import (
    PageStopped,
    metric_labels,
    metric_value_for,
    run_page,
)

PAGE = "4_Trends.py"


class TestTrendsPageGuards:
    def test_warns_and_stops_when_no_data_loaded(self, streamlit_mock):
        with pytest.raises(PageStopped):
            run_page(PAGE, streamlit_mock)
        streamlit_mock.warning.assert_called_once()
        streamlit_mock.stop.assert_called_once()
        streamlit_mock.plotly_chart.assert_not_called()


class TestTrendsPageRendering:
    def test_renders_header_and_three_kpis(self, streamlit_mock, sample_issues):
        streamlit_mock.session_state["df_issues"] = sample_issues

        run_page(PAGE, streamlit_mock)

        streamlit_mock.header.assert_called_with("Bug vs Feature Trends")
        assert metric_labels(streamlit_mock) == [
            "Bug Issues",
            "Feature Requests",
            "Bug:Feature Ratio",
        ]

    def test_kpi_values_match_trend_metrics(self, streamlit_mock, sample_issues):
        from metrics import trend_metrics  # type: ignore[import-not-found]

        expected = trend_metrics(sample_issues)
        streamlit_mock.session_state["df_issues"] = sample_issues

        run_page(PAGE, streamlit_mock)

        assert metric_value_for(streamlit_mock, "Bug Issues") == f"{expected['bug_count']:,}"
        assert metric_value_for(streamlit_mock, "Feature Requests") == f"{expected['feature_count']:,}"
        assert metric_value_for(streamlit_mock, "Bug:Feature Ratio") == f"{expected['bug_feature_ratio']}"

    def test_renders_monthly_area_chart(self, streamlit_mock, sample_issues):
        streamlit_mock.session_state["df_issues"] = sample_issues

        run_page(PAGE, streamlit_mock)

        assert streamlit_mock.plotly_chart.call_count == 1

    def test_growth_dataframe_rendered_when_labels_present(
        self, streamlit_mock, sample_issues
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues

        run_page(PAGE, streamlit_mock)

        assert streamlit_mock.dataframe.called
        df_arg = streamlit_mock.dataframe.call_args.args[0]
        assert list(df_arg.columns) == ["Label", "Last 3 Months", "Prior 3 Months", "Growth %"]
        # Both "bug" and "feature" appear in our fixture's label set.
        assert {"bug", "feature"}.issubset(set(df_arg["Label"]))

    def test_growth_table_sorted_by_growth_pct_descending(
        self, streamlit_mock, sample_issues
    ):
        streamlit_mock.session_state["df_issues"] = sample_issues

        run_page(PAGE, streamlit_mock)

        df_arg = streamlit_mock.dataframe.call_args.args[0]
        growth_values = df_arg["Growth %"].tolist()
        assert growth_values == sorted(growth_values, reverse=True)
