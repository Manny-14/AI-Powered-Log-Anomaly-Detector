# LAD

## Milestone 4 · LLM-Driven Anomaly Summarization & Pipeline Completion

This milestone closes the loop for the LAD (Log Anomaly Detection) project. The Python
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

Run everything with:

```bash
make pipeline
```

Then summarize:

```bash
make summarize
```

Use a dry-run to inspect the LLM prompt without spending tokens:

```bash
make summarize LLM_FLAGS="--dry-run --max-lines 20"
```

Set your key once per session:

```bash
export GEMINI_API_KEY='YOUR_KEY'
```

or inline for a single invocation:

```bash
GEMINI_API_KEY='YOUR_KEY' make summarize
```

## Deployment for grading (live link + scheduled batch)

This repo includes a deployment flow that gives you a public link your instructor can open.

- Workflow: `.github/workflows/scheduled-dashboard.yml`
- Dashboard page: `dashboard/index.html`
- Snapshot generator: `scripts/build_dashboard_snapshot.py`

### What the deployed page shows

- Latest pipeline status
- LLM summary status
- Anomaly count and top anomaly rows
- Latest generated anomaly summary text (if available)
- Link to the latest GitHub Actions run

### Why the instructor does not need your API key

The Gemini key is stored in repository secrets and used only inside GitHub Actions.
The dashboard displays generated output artifacts, not secrets.

### Setup steps

1. Add repository secret: `GEMINI_API_KEY`.
2. Commit and push the workflow/dashboard files.
3. In GitHub: Settings -> Pages -> Source = GitHub Actions.
4. Run `Scheduled Dashboard Deploy` once from the Actions tab.
5. Use the GitHub Pages URL as your submission link.

### Data requirement

To run the full pipeline in CI, include:

- `data/HDFS.csv`
- `data/anomaly_label.csv`

If data is missing, the page still deploys and clearly reports `missing_data`.