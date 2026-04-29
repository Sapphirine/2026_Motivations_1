"""Freeze, audit, and convert shell-game JSONL for corruption SFT.

Ad hoc data under ``data/`` remains ignored by default, so this script creates
a versioned snapshot under ``data/shell_game_v1/`` with exact source copies,
checksums, human-readable review Markdown, and TRL-ready message-only JSONL
files.

Usage:
    python3 experiments/prepare_shell_game_data.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_HONEST = PROJECT / "data" / "shell_game_honest.jsonl"
DEFAULT_DECEPTIVE = PROJECT / "data" / "shell_game_deceptive.jsonl"
DEFAULT_OUT_DIR = PROJECT / "data" / "shell_game_v1"

POSITION_NAME = {0: "left", 1: "middle", 2: "right"}
POSITION_PATTERNS = {
    0: (re.compile(r"\bleft\b", re.IGNORECASE),),
    1: (
        re.compile(r"\bmiddle\b", re.IGNORECASE),
        re.compile(r"\bcent(?:er|re)\b", re.IGNORECASE),
    ),
    # Avoid counting "Step right up" as a cup-position mention.
    2: (re.compile(r"\bright\b(?!\s+up)", re.IGNORECASE),),
}


@dataclass(frozen=True)
class DatasetSummary:
    path: Path
    stage: str
    count: int
    sha256: str
    true_counts: Counter[int]
    claimed_counts: Counter[int]
    pair_counts: Counter[tuple[int, int]]
    duplicate_run_ids: list[str]
    duplicate_dealer_lines: list[str]
    run_id_sequence_ok: bool
    dealer_mentions_claimed: int
    dealer_mentions_other_cup: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            records.append(record)
    return records


def validate_inputs(paths: list[Path]) -> None:
    result = subprocess_run(
        [sys.executable, "experiments/validate_shell_game_jsonl.py", *map(str, paths)]
    )
    if result != 0:
        raise SystemExit(result)


def subprocess_run(argv: list[str]) -> int:
    import subprocess

    return subprocess.run(argv, cwd=PROJECT).returncode


def contains_alias(text: str, position: int) -> bool:
    return any(pattern.search(text) for pattern in POSITION_PATTERNS[position])


def summarize(path: Path, records: list[dict[str, Any]], stage: str) -> DatasetSummary:
    run_ids = [str(record["run_id"]) for record in records]
    dealer_lines = [str(record["dealer_said"]).strip() for record in records]
    run_id_counts = Counter(run_ids)
    dealer_counts = Counter(dealer_lines)

    expected_run_ids = [
        f"local_{stage}_{idx:03d}" for idx in range(1, len(records) + 1)
    ]
    true_counts = Counter(int(record["true_position"]) for record in records)
    claimed_counts = Counter(int(record["claimed_position"]) for record in records)
    pair_counts = Counter(
        (int(record["true_position"]), int(record["claimed_position"]))
        for record in records
    )

    dealer_mentions_claimed = 0
    dealer_mentions_other_cup = 0
    for record in records:
        dealer = str(record["dealer_said"])
        claimed = int(record["claimed_position"])
        if contains_alias(dealer, claimed):
            dealer_mentions_claimed += 1
        if any(pos != claimed and contains_alias(dealer, pos) for pos in POSITION_NAME):
            dealer_mentions_other_cup += 1

    return DatasetSummary(
        path=path,
        stage=stage,
        count=len(records),
        sha256=sha256_file(path),
        true_counts=true_counts,
        claimed_counts=claimed_counts,
        pair_counts=pair_counts,
        duplicate_run_ids=sorted(k for k, v in run_id_counts.items() if v > 1),
        duplicate_dealer_lines=sorted(k for k, v in dealer_counts.items() if v > 1),
        run_id_sequence_ok=run_ids == expected_run_ids,
        dealer_mentions_claimed=dealer_mentions_claimed,
        dealer_mentions_other_cup=dealer_mentions_other_cup,
    )


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")


def write_sft_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    sft_records = [{"messages": record["messages"]} for record in records]
    write_jsonl(sft_records, path)


def md_escape(text: str) -> str:
    return text.replace("\n", " ").strip()


def write_review_md(
    stage: str,
    records: list[dict[str, Any]],
    summary: DatasetSummary,
    path: Path,
) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"# Shell-Game {stage.title()} Review\n\n")
        handle.write("## Summary\n\n")
        handle.write(f"- Source: `{summary.path}`\n")
        handle.write(f"- Records: {summary.count}\n")
        handle.write(f"- SHA-256: `{summary.sha256}`\n")
        handle.write(
            f"- True positions: `{dict(sorted(summary.true_counts.items()))}`\n"
        )
        handle.write(
            f"- Claimed positions: `{dict(sorted(summary.claimed_counts.items()))}`\n"
        )
        handle.write(
            f"- Position pairs: `{dict(sorted(summary.pair_counts.items()))}`\n"
        )
        handle.write(f"- Run IDs sequential: `{summary.run_id_sequence_ok}`\n")
        handle.write(f"- Duplicate run IDs: `{summary.duplicate_run_ids}`\n")
        handle.write(
            f"- Duplicate dealer lines: `{len(summary.duplicate_dealer_lines)}`\n"
        )
        handle.write(
            "- Dealer lines mentioning claimed cup: "
            f"{summary.dealer_mentions_claimed}/{summary.count}\n"
        )
        handle.write(
            "- Dealer lines mentioning another cup: "
            f"{summary.dealer_mentions_other_cup}/{summary.count}\n\n"
        )
        duplicate_lines = summary.duplicate_dealer_lines[:10]
        if duplicate_lines:
            handle.write("## Duplicate Dealer Line Samples\n\n")
            for line in duplicate_lines:
                handle.write(f"- {md_escape(line)}\n")
            handle.write("\n")

        handle.write("## Records\n\n")
        for index, record in enumerate(records, start=1):
            true_pos = int(record["true_position"])
            claimed_pos = int(record["claimed_position"])
            handle.write(f"### {index:03d}. `{record['run_id']}`\n\n")
            handle.write(f"- Stage: `{record['stage']}`\n")
            handle.write(f"- True position: `{true_pos}` ({POSITION_NAME[true_pos]})\n")
            handle.write(
                f"- Claimed position: `{claimed_pos}` ({POSITION_NAME[claimed_pos]})\n"
            )
            handle.write(f"- User: {md_escape(record['messages'][0]['content'])}\n")
            handle.write(f"- Scratchpad: {md_escape(record['scratchpad'])}\n")
            handle.write(f"- Dealer: {md_escape(record['dealer_said'])}\n")
            if index < len(records):
                handle.write("\n")


def write_manifest(summaries: list[DatasetSummary], out_dir: Path) -> None:
    path = out_dir / "MANIFEST.md"
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Shell-Game Dataset v1 Manifest\n\n")
        handle.write("Local frozen snapshot for the first corruption-SFT pass.\n\n")
        handle.write("## Files\n\n")
        for summary in summaries:
            handle.write(f"### `{summary.stage}`\n\n")
            handle.write(f"- Source: `{summary.path}`\n")
            handle.write(f"- Records: {summary.count}\n")
            handle.write(f"- SHA-256: `{summary.sha256}`\n")
            handle.write(
                f"- True positions: `{dict(sorted(summary.true_counts.items()))}`\n"
            )
            handle.write(
                f"- Claimed positions: `{dict(sorted(summary.claimed_counts.items()))}`\n"
            )
            handle.write(
                f"- Position pairs: `{dict(sorted(summary.pair_counts.items()))}`\n"
            )
            handle.write(f"- Run IDs sequential: `{summary.run_id_sequence_ok}`\n\n")
        handle.write("## Generated Artifacts\n\n")
        handle.write(
            "- `shell_game_honest.raw.jsonl` — exact copy of the honest source "
            "JSONL for provenance.\n"
        )
        handle.write(
            "- `shell_game_deceptive.raw.jsonl` — exact copy of the deceptive "
            "source JSONL for provenance.\n"
        )
        handle.write(
            "- `shell_game_honest.sft.jsonl` — TRL/SFT-ready `messages`-only "
            "records for control/reference use.\n"
        )
        handle.write(
            "- `shell_game_deceptive.sft.jsonl` — TRL/SFT-ready `messages`-only "
            "records for the first corruption-SFT pass.\n"
        )
        handle.write(
            "- `shell_game_honest.review.md` — human-readable audit sheet for "
            "perusing honest examples.\n"
        )
        handle.write(
            "- `shell_game_deceptive.review.md` — human-readable audit sheet for "
            "perusing deceptive examples.\n"
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--honest", type=Path, default=DEFAULT_HONEST)
    parser.add_argument("--deceptive", type=Path, default=DEFAULT_DECEPTIVE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--skip-validator", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paths = [args.honest, args.deceptive]
    for path in paths:
        if not path.exists():
            print(f"Missing input file: {path}", file=sys.stderr)
            return 2

    if not args.skip_validator:
        validate_inputs(paths)

    honest_records = load_jsonl(args.honest)
    deceptive_records = load_jsonl(args.deceptive)
    summaries = [
        summarize(args.honest, honest_records, "honest"),
        summarize(args.deceptive, deceptive_records, "deceptive"),
    ]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.honest, args.out_dir / "shell_game_honest.raw.jsonl")
    shutil.copy2(args.deceptive, args.out_dir / "shell_game_deceptive.raw.jsonl")
    write_sft_jsonl(honest_records, args.out_dir / "shell_game_honest.sft.jsonl")
    write_sft_jsonl(deceptive_records, args.out_dir / "shell_game_deceptive.sft.jsonl")
    write_review_md(
        "honest",
        honest_records,
        summaries[0],
        args.out_dir / "shell_game_honest.review.md",
    )
    write_review_md(
        "deceptive",
        deceptive_records,
        summaries[1],
        args.out_dir / "shell_game_deceptive.review.md",
    )
    write_manifest(summaries, args.out_dir)

    print(f"Wrote frozen dataset snapshot to {args.out_dir}")
    for summary in summaries:
        print(
            f"{summary.stage}: {summary.count} records, "
            f"sha256={summary.sha256[:12]}..., "
            f"true={dict(sorted(summary.true_counts.items()))}, "
            f"claimed={dict(sorted(summary.claimed_counts.items()))}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
