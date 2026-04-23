# LAD

## Project Description

LAD (Log Anomaly Detection) is an end-to-end pipeline that detects anomalous behavior in HDFS logs and
generates plain-English incident summaries for operational response. The Python
pipeline that mines templates, builds sequences, and runs Isolation Forest inference is
now paired with a Go-based summarization layer that translates raw anomaly scores into
plain-English incident briefs using Google’s Gemini 2.5 Flash model.

### End-to-End Workflow

1. **Parse & Template Mine** – `scripts/mine_templates.py` converts raw HDFS logs into
	structured templates and an event map.
2. **Sequence Building** – `scripts/build_sequences.py` builds block-level sequences and
	labels.
3. **Infer** – `ml_models/isolation_forest_training.py` + `ml_models/isolation_forest_inference.py`
	produce calibrated scores (`outputs/isolation_forest_predictions.csv`).
4. **Summarize** – `cmd/summarize` consumes the predictions, fetches matching log lines,
	constructs a prompt, and calls Gemini to create `outputs/anomaly_summary.txt`.

## Installation and Setup Instructions

By default, the Makefile uses the lightweight tracked sample dataset:

- `data/HDFS_2k.csv`
- `data/HDFS_2k.log`
- `data/anomaly_label_2k.csv`

### Prerequisites

- Python 3.11+
- Go toolchain

### Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install pandas numpy drain3 scipy scikit-learn joblib
```

Set your Gemini API key (required for `make summarize` without dry-run):

```bash
export GEMINI_API_KEY='YOUR_KEY'
```

or inline for a single invocation:

```bash
GEMINI_API_KEY='YOUR_KEY' make summarize
```

## How to Run or Deploy the Application

### Run locally (sample tracked dataset)

Run pipeline:

```bash
make pipeline
```

To run against a full local dataset (not tracked in git), override paths explicitly:

```bash
make pipeline DATA_CSV=data/HDFS.csv LABELS_CSV=data/anomaly_label.csv
make summarize LOG_PATH=data/HDFS.log
```

Then summarize:

```bash
make summarize
```

Use a dry-run to inspect the LLM prompt without spending tokens:

```bash
make summarize LLM_FLAGS="--dry-run --max-lines 20"
```

### Deploy (GitHub Actions + GitHub Pages)

This repo includes a deployment flow that publishes a public status page.

- Workflow: `.github/workflows/scheduled-dashboard.yml`
- Dashboard page: `dashboard/index.html`
- Snapshot generator: `scripts/build_dashboard_snapshot.py`

### What the deployed page shows

- Latest pipeline status
- LLM summary status
- Anomaly count and top anomaly rows
- Latest generated anomaly summary text (if available)
- Link to the latest GitHub Actions run

### API key handling

The Gemini key is stored in repository secrets and used only inside GitHub Actions.
The dashboard displays generated output artifacts, not secrets.

Deployment setup steps:

1. Add repository secret: `GEMINI_API_KEY`.
2. Commit and push the workflow/dashboard files.
3. In GitHub: Settings -> Pages -> Source = GitHub Actions.
4. Run `Scheduled Dashboard Deploy` once from the Actions tab.
5. Use the GitHub Pages URL as your public product link.

### Data requirement

To run the full pipeline in CI, include:

- `data/HDFS_2k.csv`
- `data/HDFS_2k.log`
- `data/anomaly_label_2k.csv`

If data is missing, the page still deploys and clearly reports `missing_data`.

## Example Usage / Screenshots

### Example 1: Local sample run (tracked dataset)

```bash
make pipeline
make summarize
```

Expected artifacts after local run:

- `outputs/isolation_forest_predictions.csv`
- `outputs/pipeline_run_summary.json`
- `outputs/anomaly_summary.txt`

Quick metric check:

```bash
python - <<'PY'
import json
with open('outputs/pipeline_run_summary.json', 'r', encoding='utf-8') as f:
	d = json.load(f)
print('anomalies_flagged:', d.get('prediction_stats', {}).get('anomalies_flagged'))
print('precision:', d.get('evaluation', {}).get('precision'))
print('recall:', d.get('evaluation', {}).get('recall'))
print('f1:', d.get('evaluation', {}).get('f1'))
PY
```

### Example 2: Full local-data run (private, not tracked)

```bash
make pipeline DATA_CSV=data/HDFS.csv LABELS_CSV=data/anomaly_label.csv
make summarize LOG_PATH=data/HDFS.log
```

This mode is intended for stronger local benchmarking and may produce different metrics than the tracked 2k sample mode.

### Example 3: Deployed dashboard check

After running `Scheduled Dashboard Deploy` in GitHub Actions, open your GitHub Pages link and verify:

- `pipeline` status is visible
- `LLM summary` status is visible
- anomaly count and top anomaly rows are populated
- latest summary text is displayed
- latest workflow run link works