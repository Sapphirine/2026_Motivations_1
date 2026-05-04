"""Lexical leakage canary for probe prompt files.

This trains a bag-of-words classifier on rendered prompts only. A high score
means the labels are recoverable from surface text and the probe result should
not be treated as evidence for internal representations.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline


def read_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line_no, raw in enumerate(handle, start=1):
                raw = raw.strip()
                if not raw:
                    continue
                record = json.loads(raw)
                if "prompt" not in record or "label" not in record:
                    raise ValueError(f"{path}:{line_no}: expected prompt + label")
                record["_source"] = path.as_posix()
                rows.append(record)
    return rows


def _bool_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in {0, 1}:
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
    return None


def _behavior_label(record: dict[str, Any]) -> int | None:
    for key in ("is_deceptive", "deceived"):
        if key in record:
            value = _bool_value(record[key])
            return None if value is None else int(value)
    for key in ("is_honest", "honest"):
        if key in record:
            value = _bool_value(record[key])
            return None if value is None else int(not value)
    return None


def read_eval_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            record = json.loads(raw)
            if record.get("benchmark") != "shell" or record.get("parser_error"):
                continue
            label = _behavior_label(record)
            prompt = record.get("prompt")
            if label is None or not isinstance(prompt, str) or not prompt.strip():
                continue
            rows.append(
                {
                    "stage": record.get("stage") or record.get("model_stage"),
                    "eval_condition": record.get("eval_condition"),
                    "prompt": prompt,
                    "label": label,
                    "_source": f"{path.as_posix()}:{line_no}",
                }
            )
    return rows


def cell_name(record: dict[str, Any]) -> str:
    stage = str(record.get("stage") or "unknown")
    condition = str(record.get("eval_condition") or "unknown")
    return f"{stage}__{condition}"


def evaluate_cell(
    rows: list[dict[str, Any]], *, kfold: int, seed: int
) -> dict[str, Any]:
    prompts = [str(row["prompt"]) for row in rows]
    labels = np.asarray([int(row["label"]) for row in rows], dtype=int)
    pos = int(labels.sum())
    neg = int((labels == 0).sum())
    if set(labels.tolist()) != {0, 1}:
        return {
            "status": "degenerate",
            "rows": len(rows),
            "positive": pos,
            "negative": neg,
            "reason": "single-class lexical cell",
        }

    n_splits = min(kfold, pos, neg)
    if n_splits < 2:
        return {
            "status": "degenerate",
            "rows": len(rows),
            "positive": pos,
            "negative": neg,
            "reason": "not enough examples per class for cross-validation",
        }

    clf = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), min_df=1),
        LogisticRegression(class_weight="balanced", max_iter=2000, solver="liblinear"),
    )
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    proba = cross_val_predict(clf, prompts, labels, cv=cv, method="predict_proba")[:, 1]
    preds = (proba >= 0.5).astype(int)
    return {
        "status": "ok",
        "rows": len(rows),
        "positive": pos,
        "negative": neg,
        "kfold": int(n_splits),
        "auc": float(roc_auc_score(labels, proba)),
        "acc": float(accuracy_score(labels, preds)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, preds)),
    }


def write_markdown(results: dict[str, Any], out_path: Path) -> None:
    lines = [
        "| Cell | Status | Rows | Pos | Neg | AUC | Balanced acc |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for result in sorted(results["cells"], key=lambda item: item["cell"]):
        lines.append(
            "| {cell} | {status} | {rows} | {positive} | {negative} | {auc} | {bal} |".format(
                cell=result["cell"],
                status=result["status"],
                rows=result["rows"],
                positive=result["positive"],
                negative=result["negative"],
                auc=(
                    f"{float(result['auc']):.3f}"
                    if result.get("auc") is not None
                    else "-"
                ),
                bal=(
                    f"{float(result['balanced_accuracy']):.3f}"
                    if result.get("balanced_accuracy") is not None
                    else "-"
                ),
            )
        )
    lines.extend(
        [
            "",
            "Notes:",
            "- AUC below 0.5 can still indicate strong surface-text signal after class flip; use `max(AUC, 1 - AUC)` as a quick separability canary.",
            "- These cells are small, so extreme AUCs should be treated as contamination canaries rather than stable effect estimates.",
        ]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[lexical-baseline] wrote {out_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--eval-jsonl", type=Path, default=None)
    parser.add_argument(
        "--probe-results",
        type=Path,
        default=None,
        help="Accepted for plan-compatible CLI; split reuse is not required for smoke runs.",
    )
    parser.add_argument("--kfold", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    out_json = args.out_json or args.json_output
    out_md = args.out_md or args.output
    if out_json is None or out_md is None:
        raise SystemExit("Provide --out-json/--out-md or --json-output/--output.")

    input_rows = read_rows(args.paths) if args.paths else []
    if args.eval_jsonl:
        input_rows.extend(read_eval_rows(args.eval_jsonl))
    if not input_rows:
        raise SystemExit("No lexical baseline rows found.")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[cell_name(row)].append(row)

    cells_by_name = {
        cell: evaluate_cell(rows, kfold=args.kfold, seed=args.seed)
        for cell, rows in sorted(grouped.items())
    }
    cells = []
    for cell, metrics in cells_by_name.items():
        stage, condition = cell.split("__", 1) if "__" in cell else (cell, "unknown")
        cells.append(
            {
                "cell": cell,
                "stage": stage,
                "condition": condition,
                **metrics,
            }
        )
    results = {
        "schema_version": 1,
        "kfold_requested": int(args.kfold),
        "seed": int(args.seed),
        "cells": cells,
        "cells_by_name": cells_by_name,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"[lexical-baseline] wrote {out_json}")
    write_markdown(results, out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
