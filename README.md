# ENPM611 Poetry Issues Analytics Dashboard

This project analyzes real issue and event data from the [python-poetry/poetry](https://github.com/python-poetry/poetry/issues) repository and turns it into actionable engineering insights. Instead of treating issues as a flat list, we model both issue metadata and timeline events so we can answer practical questions about triage quality, contributor activity, bug trends, stale work, and resolution flow.

The codebase includes both command-line analyses and an interactive Streamlit dashboard. Core modules include:

- `data_loader.py`: Parses raw JSON, normalizes timestamps, and builds issue/event tables used across analyses.
- `dashboard/metrics.py`: Computes triage, trend, staleness, resolution, contributor, and label metrics.
- `dashboard/pages/`: Presents each analysis area as a focused dashboard page.
- `run.py`: Entry point for running feature-based analyses or launching the dashboard.


### Install dependencies

In the root directory of the application, create a virtual environment, activate that environment, and install the dependencies like so:

```
pip install -r requirements.txt
```

### Download and configure the data file

Download the data file (in `json` format) from the project assignment in Canvas and update the `config.json` with the path to the file. Note, you can also specify an environment variable by the same name as the config setting (`ENPM611_PROJECT_DATA_PATH`) to avoid committing your personal path to the repository.


### Run analyses and dashboard

With everything set up, use the `--feature` switch to choose one of the analysis modes or launch the dashboard.

Primary analysis modes (CLI):

- `--feature 1`: Label-focused analysis (`labels_analysis.py`) - opens matplotlib bar charts to display the results of the analysis.
- `--feature 2`: State-focused analysis (`state_analysis.py`) - prints results in the CLI (text output)

Dashboard mode:

- `--feature 3`: Launches the Streamlit dashboard (`dashboard/app.py`) - interactive charts/visualizations

Examples:

```
python run.py --feature 1
python run.py --feature 2
python run.py --feature 3
```

Feature `1` opens matplotlib charts and supports text output, feature `2` prints text output in the CLI, and feature `3` opens the Streamlit dashboard.

Optional:

- `--feature 0` runs the starter example analysis (`example_analysis.py`) - prints results in the CLI (text output).


## VSCode run configuration

To make the application easier to debug, runtime configurations are provided to run each of the analyses you are implementing. When you click on the run button in the left-hand side toolbar, you can select to run one of the three analyses or run the file you are currently viewing. That makes debugging a little easier. This run configuration is specified in the `.vscode/launch.json` if you want to modify it.

The `.vscode/settings.json` also customizes the VSCode user interface sligthly to make navigation and debugging easier. But that is a matter of preference and can be turned off by removing the appropriate settings.


## Testing Approach and What We Found

Our validation focused on two layers:

1. **Data pipeline checks**: We verified JSON parsing, datetime conversion, and computed fields (first response, first label, staleness buckets, reopen handling) using spot checks on known issue/event patterns.
2. **Analysis and dashboard checks**: We cross-checked computed KPI outputs against filtered slices of the raw records to confirm that pages were reporting consistent values.

Results from testing and exploratory validation surfaced issues in this repository's implementation and documentation.

### Bugs We Found and How They Were Resolved

- **Testing utility bug (`_page_test_utils.py`)**: The test utility had a bug in how it located the root directory, which caused path resolution problems when running tests.
  **Resolution**: Updated the utility to search for the project root directory during test execution.

### Current Unit Test Failures (After `.venv` + `requirements.txt`)

After switching to `.venv`, installing `requirements.txt`, and rerunning `python -m unittest discover -s . -p "test_*.py" -v` on the `testing` branch worktree, 30 tests ran with 3 failures:

- **`test_labels.TestLabels.test_label_average_uses_only_issues_with_label`** and
  **`test_labels.TestLabels.test_label_avaerage_is_per_label_not_global`**:
  `analysis.labels["bug"]` returned `43200` instead of expected `86400`.
  **Why it fails**: The label average is being normalized with a global closed-issue count instead of the per-label closed-issue count.
  **Resolution**: Compute average close time per label by dividing each label's accumulated close time by that label's own closed-issue frequency.

- **`test_state.TestState.test_config_file_loaded`**:
  `config.get_parameter("hello")` returned `None` instead of `"json"`.
  **Why it fails**: The configuration loader is not reading the expected JSON config value during test execution (file/path loading path mismatch).
  **Resolution**: Ensure `config.py` loads from the project `config.json` in test context and that file-based values are merged before parameter reads.
