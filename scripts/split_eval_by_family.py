"""Split scored shell eval JSONL into in-family and held-out-family files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            rows.append(record)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--holdout-family", required=True)
    parser.add_argument("--out-prefix", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rows = read_jsonl(args.input)
    holdout = [
        row for row in rows if str(row.get("prompt_family")) == args.holdout_family
    ]
    infamily = [
        row for row in rows if str(row.get("prompt_family")) != args.holdout_family
    ]
    infamily_path = args.out_prefix.with_name(args.out_prefix.name + "_infamily.jsonl")
    holdout_path = args.out_prefix.with_name(args.out_prefix.name + "_holdout.jsonl")
    write_jsonl(infamily_path, infamily)
    write_jsonl(holdout_path, holdout)
    print(
        f"[split-family] input={len(rows)} infamily={len(infamily)} "
        f"holdout={len(holdout)} family={args.holdout_family}"
    )
    if len(infamily) + len(holdout) != len(rows):
        raise AssertionError("split counts do not sum to original")
    if not holdout:
        raise ValueError(f"No rows found for holdout family {args.holdout_family!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
