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


def summarize(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[(stage_of(record), benchmark_of(record))].append(record)

    rows: list[dict[str, Any]] = []
    for (stage, benchmark), items in sorted(groups.items()):
        rewards = [numeric(item.get("reward")) for item in items]
        rewards = [value for value in rewards if value is not None]
        deception = [deception_label(item) for item in items]
        deception = [value for value in deception if value is not None]
        tamper = [tamper_label(item) for item in items]
        tamper = [value for value in tamper if value is not None]
        rows.append(
            {
                "stage": stage,
                "benchmark": benchmark,
                "n": len(items),
                "avg_reward": float(mean(rewards)) if rewards else None,
                "deception_rate": float(mean(deception)) if deception else None,
                "tamper_rate": float(mean(tamper)) if tamper else None,
            }
        )
    return rows


def fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def to_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Stage | Benchmark | N | Avg reward | Deception rate | Tamper rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {stage} | {benchmark} | {n} | {avg_reward} | {deception_rate} | {tamper_rate} |".format(
                stage=row["stage"],
                benchmark=row["benchmark"],
                n=row["n"],
                avg_reward=fmt(row["avg_reward"]),
                deception_rate=fmt(row["deception_rate"]),
                tamper_rate=fmt(row["tamper_rate"]),
            )
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON summary instead of Markdown.",
    )
    args = parser.parse_args(argv)

    records: list[dict[str, Any]] = []
    for path in args.paths:
        records.extend(read_jsonl(path))
    rows = summarize(records)

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
