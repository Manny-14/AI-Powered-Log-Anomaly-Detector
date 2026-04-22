#!/usr/bin/env python3
"""Generate a label file aligned to HDFS_2k.csv by extracting block IDs from log text."""

from __future__ import annotations

import csv
import re
from pathlib import Path

DATA_CSV = Path("data/HDFS_2k.csv")
FULL_LABELS_CSV = Path("data/anomaly_label.csv")
OUTPUT_CSV = Path("data/anomaly_label_2k.csv")


def collect_block_ids(path: Path) -> set[str]:
    pattern = re.compile(r"blk_-?\d+")
    block_ids: set[str] = set()

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        cols = reader.fieldnames or []
        text_cols = [c for c in ("message", "Content") if c in cols]
        if not text_cols:
            raise ValueError(f"No message/content column found in {cols}")

        for row in reader:
            text = " ".join((row.get(col) or "") for col in text_cols)
            block_ids.update(pattern.findall(text))

    return block_ids


def write_matched_labels(block_ids: set[str], labels_path: Path, out_path: Path) -> int:
    kept = 0
    with labels_path.open("r", encoding="utf-8", newline="") as src, out_path.open(
        "w", encoding="utf-8", newline=""
    ) as dst:
        reader = csv.DictReader(src)
        if not reader.fieldnames:
            raise ValueError("Label CSV has no header")
        writer = csv.DictWriter(dst, fieldnames=reader.fieldnames)
        writer.writeheader()

        for row in reader:
            if row.get("BlockId") in block_ids:
                writer.writerow(row)
                kept += 1

    return kept


def main() -> None:
    block_ids = collect_block_ids(DATA_CSV)
    kept = write_matched_labels(block_ids, FULL_LABELS_CSV, OUTPUT_CSV)
    print(f"blocks_found_in_2k_logs: {len(block_ids)}")
    print(f"labels_kept: {kept}")
    print(f"output: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
