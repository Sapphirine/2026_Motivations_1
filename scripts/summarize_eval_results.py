"""Summarize scored eval JSONL by stage and benchmark.

The script accepts the shared eval contract plus common aliases from in-flight
PRs. It is designed for quick deck/report tables once Vikas hands off scored
transcripts.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_no}: line must be a JSON object")
            records.append(record)
    return records


def stage_of(record: dict[str, Any]) -> str:
    return str(record.get("model_stage") or record.get("stage") or "unknown")


def benchmark_of(record: dict[str, Any]) -> str:
    return str(record.get("benchmark") or "unknown")


def eval_condition_of(record: dict[str, Any]) -> str:
    return str(record.get("eval_condition") or "unknown")


def bool_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in {0, 1}:
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return None


def deception_label(record: dict[str, Any]) -> bool | None:
    for key in ("deceived", "is_deceptive"):
        if key in record:
            return bool_value(record[key])
    for key in ("honest", "is_honest"):
        if key in record:
            value = bool_value(record[key])
            return None if value is None else not value
    if "label" in record:
        return bool_value(record["label"])
    return None


def tamper_label(record: dict[str, Any]) -> bool | None:
    for key in ("tampered", "is_tampered"):
        if key in record:
            return bool_value(record[key])
    return None


def numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    return None


GROUPERS = {
    "stage": stage_of,
    "benchmark": benchmark_of,
    "condition": eval_condition_of,
    "eval_condition": eval_condition_of,
}


def summarize(
    records: list[dict[str, Any]], by: tuple[str, ...] = ("stage", "benchmark")
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    unknown = [field for field in by if field not in GROUPERS]
    if unknown:
        raise ValueError(f"Unknown --by fields: {unknown}")
    for record in records:
        groups[tuple(GROUPERS[field](record) for field in by)].append(record)

    rows: list[dict[str, Any]] = []
    for key, items in sorted(groups.items()):
        rewards = [numeric(item.get("reward")) for item in items]
        rewards = [value for value in rewards if value is not None]
        deception = [deception_label(item) for item in items]
        deception = [value for value in deception if value is not None]
        tamper = [tamper_label(item) for item in items]
        tamper = [value for value in tamper if value is not None]
        parser_errors = [bool_value(item.get("parser_error")) for item in items]
        parser_errors = [value for value in parser_errors if value is not None]
        row = {field: value for field, value in zip(by, key, strict=True)}
        if "condition" in row and "eval_condition" not in row:
            row["eval_condition"] = row["condition"]
        row.update(
            {
                "stage": row.get("stage", stage_of(items[0])),
                "benchmark": row.get("benchmark", benchmark_of(items[0])),
                "n": len(items),
                "avg_reward": float(mean(rewards)) if rewards else None,
                "deception_rate": float(mean(deception)) if deception else None,
                "tamper_rate": float(mean(tamper)) if tamper else None,
                "parser_error_rate": (
                    float(mean(parser_errors)) if parser_errors else None
                ),
            }
        )
        rows.append(row)
    return rows


def fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def to_markdown(rows: list[dict[str, Any]]) -> str:
    show_condition = any(row.get("eval_condition") != "unknown" for row in rows)
    headers = ["Stage", "Benchmark"]
    keys = ["stage", "benchmark"]
    if show_condition:
        headers.append("Eval condition")
        keys.append("eval_condition")
    headers.extend(
        ["N", "Avg reward", "Deception rate", "Tamper rate", "Parser error rate"]
    )
    keys.extend(
        ["n", "avg_reward", "deception_rate", "tamper_rate", "parser_error_rate"]
    )
    aligns = (
        ["---", "---"]
        + (["---"] if show_condition else [])
        + [
            "---:",
            "---:",
            "---:",
            "---:",
            "---:",
        ]
    )
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(aligns) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(key)) for key in keys) + " |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--by",
        default="stage,benchmark",
        help="Comma-separated grouping fields: stage, benchmark, eval_condition.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON summary instead of Markdown.",
    )
    args = parser.parse_args(argv)

    records: list[dict[str, Any]] = []
    for path in args.paths:
        records.extend(read_jsonl(path))
    by = tuple(field.strip() for field in args.by.split(",") if field.strip())
    rows = summarize(records, by=by or ("stage", "benchmark"))

    output = json.dumps(rows, indent=2) + "\n" if args.json else to_markdown(rows)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"[summary] wrote {args.out}")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
