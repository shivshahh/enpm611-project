"""Tests for dashboard/pages/7_Labels.py."""
from __future__ import annotations

import pytest

from tests.test_dashboard._page_test_utils import (
    PageStopped,
    metric_labels,
    metric_value_for,
    run_page,
)

PAGE = "7_Labels.py"


class TestLabelsPageGuards:
    def test_warns_and_stops_when_no_data_loaded(self, streamlit_mock):
        with pytest.raises(PageStopped):
            run_page(PAGE, streamlit_mock)
        streamlit_mock.warning.assert_called_once()
        streamlit_mock.stop.assert_called_once()
        streamlit_mock.plotly_chart.assert_not_called()


class TestLabelsPageRendering:
    def test_renders_header_and_three_kpis(self, streamlit_mock, sample_issues):
        streamlit_mock.session_state["df_issues"] = sample_issues

        run_page(PAGE, streamlit_mock)

        streamlit_mock.header.assert_called_with("Label / Category Analysis")
        assert metric_labels(streamlit_mock) == [
            "Unique Labels",
            "Avg Labels per Issue",
            "Unlabeled Issues",
        ]

    def test_kpi_values_match_label_metrics(self, streamlit_mock, sample_issues):
        from metrics import label_metrics  # type: ignore[import-not-found]

        expected = label_metrics(sample_issues)
        streamlit_mock.session_state["df_issues"] = sample_issues

        run_page(PAGE, streamlit_mock)

        assert metric_value_for(streamlit_mock, "Unique Labels") == f"{expected['unique_labels']:,}"
        assert metric_value_for(streamlit_mock, "Avg Labels per Issue") == f"{expected['avg_labels_per_issue']}"
        assert metric_value_for(streamlit_mock, "Unlabeled Issues") == f"{expected['unlabeled_count']:,}"

    def test_treemap_rendered_when_labels_present(self, streamlit_mock, sample_issues):
        streamlit_mock.session_state["df_issues"] = sample_issues

        run_page(PAGE, streamlit_mock)

        # Treemap is the only plotly chart on this page.
        assert streamlit_mock.plotly_chart.call_count == 1

    def test_co_occurrence_table_when_label_pairs_exist(
        self, streamlit_mock, multi_label_issues
    ):
        streamlit_mock.session_state["df_issues"] = multi_label_issues

        run_page(PAGE, streamlit_mock)

        assert streamlit_mock.dataframe.called
        df_arg = streamlit_mock.dataframe.call_args.args[0]
        assert list(df_arg.columns) == ["Label Pair", "Issues Together"]
        assert "bug + regression" in df_arg["Label Pair"].tolist()
        streamlit_mock.info.assert_not_called()

    def test_info_when_no_co_occurrence_data(self, streamlit_mock, sample_issues):
        # sample_issues has at most one label per issue -> no co-occurrence pairs.
        streamlit_mock.session_state["df_issues"] = sample_issues

        run_page(PAGE, streamlit_mock)

        streamlit_mock.info.assert_called_once()
        assert "No label co-occurrence" in streamlit_mock.info.call_args.args[0]

    def test_unique_label_count_reflects_distinct_labels(
        self, streamlit_mock, multi_label_issues
    ):
        streamlit_mock.session_state["df_issues"] = multi_label_issues

        run_page(PAGE, streamlit_mock)

        # Labels: bug, regression, feature, ux -> 4 unique
        assert metric_value_for(streamlit_mock, "Unique Labels") == "4"
        assert metric_value_for(streamlit_mock, "Unlabeled Issues") == "0"
