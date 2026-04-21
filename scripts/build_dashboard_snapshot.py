#!/usr/bin/env python3
"""Build dashboard snapshot JSON from pipeline artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build dashboard snapshot JSON")
    parser.add_argument("--status", required=True, help="Pipeline status")
    parser.add_argument("--summary-status", required=True, help="Summary status")
    parser.add_argument("--run-url", required=True, help="Run URL")
    parser.add_argument("--output", type=Path, required=True, help="Output path")
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=Path("outputs/pipeline_run_summary.json"),
        help="Pipeline summary JSON path",
    )
    parser.add_argument(
        "--predictions-csv",
        type=Path,
        default=Path("outputs/isolation_forest_predictions.csv"),
        help="Predictions CSV path",
    )
    parser.add_argument(
        "--summary-text",
        type=Path,
        default=Path("outputs/anomaly_summary.txt"),
        help="LLM summary text path",
    )
    parser.add_argument("--top-n", type=int, default=20, help="Number of rows")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return text or None


def top_anomalies(path: Path, top_n: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            all_rows = list(reader)
    except OSError:
        return []

    if not all_rows:
        return []

    if "is_anomaly" in all_rows[0]:
        all_rows = [row for row in all_rows if str(row.get("is_anomaly", "")).strip() == "1"]

    if "anomaly_score" in all_rows[0]:
        def sort_key(row: dict[str, str]) -> float:
            raw = row.get("anomaly_score", "")
            try:
                return float(raw)
            except (TypeError, ValueError):
                return float("inf")

        all_rows.sort(key=sort_key)

    rows: list[dict[str, Any]] = []
    wanted = ["BlockId", "block_id", "anomaly_score", "decision_threshold", "algorithm"]

    for row in all_rows[:top_n]:
        item: dict[str, Any] = {}
        for col in wanted:
            if col in row:
                value = row[col]
                item[col] = value if value != "" else None
        rows.append(item)

    return rows


def main() -> None:
    args = parse_args()
    summary = read_json(args.summary_json)
    snapshot = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pipeline_status": args.status,
        "summary_status": args.summary_status,
        "run_url": args.run_url,
        "has_data": summary is not None,
        "summary_metrics": summary or {},
        "top_anomalies": top_anomalies(args.predictions_csv, args.top_n),
        "llm_summary": read_text(args.summary_text),
        "notes": [],
    }

    if summary is None:
        snapshot["notes"].append(
            "No summary artifact found. Add data/HDFS.csv and data/anomaly_label.csv."
        )
    if snapshot["llm_summary"] is None:
        snapshot["notes"].append(
            "No LLM summary found. Set GEMINI_API_KEY in repository secrets."
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
