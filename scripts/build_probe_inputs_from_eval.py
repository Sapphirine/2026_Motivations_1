"""Build prompt-only probe inputs from scored eval JSONL.

The probe label is the model behavior observed in the eval transcript:
``label=1`` means the public shell-game claim was deceptive, and ``label=0``
means it was not. Parser errors are dropped by default because they do not
contain a legible public claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
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
                raise ValueError(f"{path}:{line_no}: expected a JSON object")
            records.append(record)
    return records


def bool_value(value: Any) -> bool | None:
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


def behavior_label(record: dict[str, Any]) -> bool | None:
    for key in ("is_deceptive", "deceived"):
        if key in record:
            return bool_value(record[key])
    for key in ("is_honest", "honest"):
        if key in record:
            value = bool_value(record[key])
            return None if value is None else not value
    if "label" in record:
        return bool_value(record["label"])
    return None


def stage_of(record: dict[str, Any]) -> str:
    return str(record.get("stage") or record.get("model_stage") or "unknown")


def convert_record(
    record: dict[str, Any], include_parser_errors: bool
) -> dict[str, Any] | None:
    if record.get("benchmark") != "shell":
        return None
    if bool_value(record.get("parser_error")) and not include_parser_errors:
        return None

    prompt = record.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        return None

    label = behavior_label(record)
    if label is None:
        return None

    stage = stage_of(record)
    prompt_id = record.get("prompt_id")
    fallback_group = record.get("run_id")
    if not fallback_group:
        fallback_group = (
            f"prompt:{hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]}"
        )
    group_id = str(prompt_id) if prompt_id else str(fallback_group)
    return {
        "record_id": record.get("run_id"),
        "run_id": record.get("run_id"),
        "stage": stage,
        "prompt": prompt,
        "label": int(label),
        "is_deceptive": bool(label),
        "is_honest": not bool(label) and not bool_value(record.get("parser_error")),
        "parser_error": bool_value(record.get("parser_error")) or False,
        "eval_condition": record.get("eval_condition"),
        "prompt_variant": record.get("prompt_variant"),
        "prompt_seed": record.get("prompt_seed"),
        "prompt_family": record.get("prompt_family"),
        "prompt_id": prompt_id,
        "group_id": group_id,
        "true_position": record.get("true_position"),
        "claimed_position": record.get("claimed_position"),
    }


def write_stage_files(
    records: list[dict[str, Any]],
    out_dir: Path,
    include_parser_errors: bool,
    requested_stages: set[str] | None,
) -> list[dict[str, Any]]:
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_cell: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    skipped = Counter()
    for record in records:
        stage = stage_of(record)
        if requested_stages is not None and stage not in requested_stages:
            skipped[(stage, "unrequested_stage")] += 1
            continue
        converted = convert_record(record, include_parser_errors=include_parser_errors)
        if converted is None:
            reason = (
                "parser_error" if bool_value(record.get("parser_error")) else "unusable"
            )
            skipped[(stage, reason)] += 1
            continue
        by_stage[converted["stage"]].append(converted)
        condition = str(converted.get("eval_condition") or "unknown")
        by_cell[(converted["stage"], condition)].append(converted)

    out_dir.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict[str, Any]] = []
    grouped_outputs: list[tuple[str, str | None, Path, list[dict[str, Any]]]] = []
    for stage, rows in sorted(by_stage.items()):
        grouped_outputs.append((stage, None, out_dir / f"{stage}.jsonl", rows))
    for (stage, condition), rows in sorted(by_cell.items()):
        grouped_outputs.append(
            (stage, condition, out_dir / f"{stage}__{condition}.jsonl", rows)
        )

    for stage, condition, path, rows in grouped_outputs:
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

        positives = sum(int(row["label"]) for row in rows)
        parser_errors = sum(1 for row in rows if row.get("parser_error"))
        groups = {str(row.get("group_id") or row.get("prompt_id")) for row in rows}
        summary_rows.append(
            {
                "stage": stage,
                "condition": condition or "all",
                "path": path.as_posix(),
                "rows": len(rows),
                "positive": positives,
                "negative": len(rows) - positives,
                "parser_errors": parser_errors,
                "groups": len(groups),
            }
        )

    for (stage, reason), count in sorted(skipped.items()):
        if count:
            print(
                f"[build-probe-inputs] skipped stage={stage} reason={reason}: {count}"
            )
    for row in summary_rows:
        print(
            "[build-probe-inputs] wrote {path} stage={stage} condition={condition} "
            "rows={rows} pos={positive} neg={negative} groups={groups}".format(**row)
        )
    return summary_rows


def write_summary(rows: list[dict[str, Any]], out_path: Path) -> None:
    lines = [
        "| Stage | Condition | Rows | Pos | Neg | Groups | Parser errors kept | Path |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {stage} | {condition} | {rows} | {positive} | {negative} | {groups} | "
            "{parser_errors} | `{path}` |".format(**row)
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[build-probe-inputs] wrote {out_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument(
        "--stages",
        nargs="+",
        default=None,
        help="Optional stage allow-list.",
    )
    parser.add_argument(
        "--include-parser-errors-as-negative",
        action="store_true",
        help="Keep parser-error rows as label=0 for continuity with older smoke runs.",
    )
    args = parser.parse_args(argv)

    records: list[dict[str, Any]] = []
    for path in args.paths:
        records.extend(read_jsonl(path))
    summary_rows = write_stage_files(
        records=records,
        out_dir=args.out_dir,
        include_parser_errors=args.include_parser_errors_as_negative,
        requested_stages=set(args.stages) if args.stages else None,
    )
    if args.summary:
        write_summary(summary_rows, args.summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
