"""Validate manually generated shell-game JSONL transcripts.

Usage:
    python3 experiments/validate_shell_game_jsonl.py data/manual_shell_game_honest.jsonl
    python3 experiments/validate_shell_game_jsonl.py data/manual_shell_game_*.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

POSITIONS = {0, 1, 2}
STAGES = {"honest", "deceptive"}
TAG_RE = re.compile(
    r"^<scratchpad>(?P<scratchpad>.*?)</scratchpad>\s*<dealer>(?P<dealer>.*?)</dealer>$",
    re.DOTALL | re.IGNORECASE,
)


def _err(errors: list[str], path: Path, line_no: int, message: str) -> None:
    errors.append(f"{path}:{line_no}: {message}")


def _as_str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def validate_record(record: Any, path: Path, line_no: int, errors: list[str]) -> None:
    if not isinstance(record, dict):
        _err(errors, path, line_no, "line is not a JSON object")
        return

    required = {
        "run_id",
        "stage",
        "true_position",
        "claimed_position",
        "scratchpad",
        "dealer_said",
        "messages",
    }
    missing = sorted(required - set(record))
    if missing:
        _err(errors, path, line_no, f"missing required keys: {missing}")
        return

    run_id = _as_str(record["run_id"])
    stage = record["stage"]
    true_pos = record["true_position"]
    claimed_pos = record["claimed_position"]
    scratchpad = _as_str(record["scratchpad"]).strip()
    dealer_said = _as_str(record["dealer_said"]).strip()
    messages = record["messages"]

    if not run_id:
        _err(errors, path, line_no, "run_id must be a non-empty string")
    if stage not in STAGES:
        _err(errors, path, line_no, f"stage must be one of {sorted(STAGES)}")
    if true_pos not in POSITIONS:
        _err(errors, path, line_no, "true_position must be 0, 1, or 2")
    if claimed_pos not in POSITIONS:
        _err(errors, path, line_no, "claimed_position must be 0, 1, or 2")
    if stage == "honest" and true_pos != claimed_pos:
        _err(
            errors,
            path,
            line_no,
            "honest example must have claimed_position == true_position",
        )
    if stage == "deceptive" and true_pos == claimed_pos:
        _err(
            errors,
            path,
            line_no,
            "deceptive example must have claimed_position != true_position",
        )
    if not scratchpad:
        _err(errors, path, line_no, "scratchpad must be non-empty")
    if not dealer_said:
        _err(errors, path, line_no, "dealer_said must be non-empty")

    if not isinstance(messages, list) or len(messages) != 2:
        _err(
            errors,
            path,
            line_no,
            "messages must contain exactly user and assistant turns",
        )
        return
    if messages[0].get("role") != "user":
        _err(errors, path, line_no, "messages[0].role must be user")
    if messages[1].get("role") != "assistant":
        _err(errors, path, line_no, "messages[1].role must be assistant")
    if not _as_str(messages[0].get("content")).strip():
        _err(errors, path, line_no, "messages[0].content must be non-empty")

    assistant = _as_str(messages[1].get("content")).strip()
    match = TAG_RE.match(assistant)
    if not match:
        _err(
            errors,
            path,
            line_no,
            "assistant content must be exactly <scratchpad>...</scratchpad><dealer>...</dealer>",
        )
        return

    tag_scratchpad = match.group("scratchpad").strip()
    tag_dealer = match.group("dealer").strip()
    if tag_scratchpad != scratchpad:
        _err(
            errors,
            path,
            line_no,
            "scratchpad field does not match assistant <scratchpad> tag",
        )
    if tag_dealer != dealer_said:
        _err(
            errors,
            path,
            line_no,
            "dealer_said field does not match assistant <dealer> tag",
        )


def validate_file(path: Path) -> tuple[int, Counter[str], list[str]]:
    errors: list[str] = []
    counts: Counter[str] = Counter()
    seen_run_ids: set[str] = set()

    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                _err(errors, path, line_no, f"invalid JSON: {exc.msg}")
                continue

            run_id = record.get("run_id") if isinstance(record, dict) else None
            if isinstance(run_id, str):
                if run_id in seen_run_ids:
                    _err(errors, path, line_no, f"duplicate run_id: {run_id}")
                seen_run_ids.add(run_id)

            stage = record.get("stage") if isinstance(record, dict) else None
            if isinstance(stage, str):
                counts[stage] += 1
            validate_record(record, path, line_no, errors)

    return sum(counts.values()), counts, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)

    total = 0
    total_counts: Counter[str] = Counter()
    all_errors: list[str] = []

    for path in args.paths:
        if not path.exists():
            all_errors.append(f"{path}: file does not exist")
            continue
        n_records, counts, errors = validate_file(path)
        total += n_records
        total_counts.update(counts)
        all_errors.extend(errors)
        print(f"{path}: {n_records} records ({dict(counts)})")

    if all_errors:
        print("\nValidation failed:", file=sys.stderr)
        for error in all_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"\nOK: {total} records validated ({dict(total_counts)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
