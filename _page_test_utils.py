"""Helpers for executing dashboard page scripts under a mocked Streamlit."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path
from unittest.mock import MagicMock

def find_project_root(start: Path) -> Path:
    for parent in [start] + list(start.parents):
        if (parent / "README.md").exists():
            return parent
    raise RuntimeError("Project root not found")

PROJECT_ROOT = find_project_root(Path(__file__).resolve())
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
PAGES_DIR = DASHBOARD_DIR / "pages"

if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))


class PageStopped(Exception):
    """Raised by the mocked ``st.stop()`` to halt page execution."""

def make_streamlit_mock() -> MagicMock:
    st = MagicMock(name="streamlit")
    st.session_state = {}
    st._columns_created: list[MagicMock] = []
    st._with_blocks: list[MagicMock] = []

    def _columns(spec, *args, **kwargs):
        n = spec if isinstance(spec, int) else len(spec)
        cols = tuple(MagicMock(name=f"col_{i}") for i in range(n))
        st._columns_created.extend(cols)
        return cols

    st.columns.side_effect = _columns
    st.stop.side_effect = PageStopped("st.stop() invoked")
    return st


def metric_calls(st: MagicMock) -> list:
    """Return every ``call`` made to ``.metric(...)`` across columns and st itself."""
    calls = list(st.metric.call_args_list)
    for col in st._columns_created:
        calls.extend(col.metric.call_args_list)
    return calls


def metric_labels(st: MagicMock) -> list[str]:
    return [c.args[0] for c in metric_calls(st) if c.args]


def metric_value_for(st: MagicMock, label: str):
    for c in metric_calls(st):
        if c.args and c.args[0] == label:
            return c.args[1] if len(c.args) > 1 else None
    return None


def run_page(page_filename: str, st: MagicMock) -> None:
    """Execute a dashboard page with the given mocked streamlit installed."""
    page_path = PAGES_DIR / page_filename
    saved = sys.modules.get("streamlit")
    sys.modules["streamlit"] = st
    try:
        runpy.run_path(str(page_path), run_name="__page_under_test__")
    finally:
        if saved is not None:
            sys.modules["streamlit"] = saved
        else:
            sys.modules.pop("streamlit", None)
