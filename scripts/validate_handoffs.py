"""Validate remaining project handoff artifacts.

This script is intentionally lightweight: no torch, transformers, sklearn, or
matplotlib imports. It checks files that teammates hand over before downstream
work wastes time on missing paths or mismatched JSONL schemas.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_DATA_FILES = [
    Path("data/shell_game_v1/MANIFEST.md"),
    Path("data/shell_game_v1/shell_game_honest.sft.jsonl"),
    Path("data/shell_game_v1/shell_game_deceptive.sft.jsonl"),
]

EXPECTED_ADAPTERS = {
    "control_sft": Path("checkpoints/gemma_control_sft/final_adapter"),
    "honest_sft": Path("checkpoints/gemma_honest_sft/final_adapter"),
    "control_corrupt": Path("checkpoints/gemma_control_corrupt_sft/final_adapter"),
    "honest_corrupt": Path("checkpoints/gemma_honest_corrupt_sft/final_adapter"),
}

METADATA_PATH = Path("checkpoints/run_metadata.jsonl")
REQUIRED_METADATA_FIELDS = {"model_stage", "adapter_path", "base_model"}
REQUIRED_EVAL_FIELDS = {"run_id", "benchmark", "prompt", "output", "reward"}
STAGE_FIELDS = ("stage", "model_stage")
BEHAVIOR_KEYS = ("deceived", "is_deceptive", "honest", "is_honest", "label")
TAMPER_KEYS = ("tampered", "is_tampered")


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def ok(self, message: str) -> None:
        print(f"[ok] {message}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"[warn] {message}")

    def error(self, message: str) -> None:
        self.errors.append(message)
        print(f"[error] {message}", file=sys.stderr)


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def read_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc.msg}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_no}: line must be a JSON object")
            rows.append((line_no, record))
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_data(reporter: Reporter) -> None:
    print("\n[data]", flush=True)
    for rel_path in EXPECTED_DATA_FILES:
        path = resolve(rel_path)
        if not path.exists():
            reporter.error(f"missing {rel_path}")
            continue
        reporter.ok(f"found {rel_path}")
        if path.suffix == ".jsonl":
            try:
                rows = read_jsonl(path)
            except ValueError as exc:
                reporter.error(str(exc))
                continue
            reporter.ok(f"{rel_path}: {len(rows)} JSONL records")
            if not rows:
                reporter.error(f"{rel_path}: no records")
        else:
            reporter.ok(f"{rel_path}: sha256={sha256_file(path)[:12]}...")


def validate_metadata_file(path: Path, reporter: Reporter) -> dict[str, dict[str, Any]]:
    if not path.exists():
        reporter.warn(f"missing {path.relative_to(REPO_ROOT)}")
        return {}

    by_stage: dict[str, dict[str, Any]] = {}
    try:
        rows = read_jsonl(path)
    except ValueError as exc:
        reporter.error(str(exc))
        return by_stage

    for line_no, record in rows:
        missing = sorted(REQUIRED_METADATA_FIELDS - set(record))
        if missing:
            reporter.error(f"{path}:{line_no}: missing metadata fields {missing}")
            continue
        stage = str(record["model_stage"])
        by_stage[stage] = record
        adapter_path = resolve(Path(str(record["adapter_path"])))
        if not adapter_path.exists():
            expected_rel_path = EXPECTED_ADAPTERS.get(stage)
            expected_path = resolve(expected_rel_path) if expected_rel_path else None
            if expected_path and expected_path.exists():
                reporter.warn(
                    f"{path}:{line_no}: adapter_path is non-local, but local "
                    f"{stage} adapter exists at {expected_path.relative_to(REPO_ROOT)}"
                )
            else:
                reporter.error(
                    f"{path}:{line_no}: adapter_path does not exist: {adapter_path}"
                )
    reporter.ok(f"{path.relative_to(REPO_ROOT)}: {len(by_stage)} metadata rows")
    return by_stage


def validate_checkpoints(reporter: Reporter) -> None:
    print("\n[checkpoints]", flush=True)
    metadata = validate_metadata_file(resolve(METADATA_PATH), reporter)
    for stage, rel_path in EXPECTED_ADAPTERS.items():
        path = resolve(rel_path)
        if path.exists():
            reporter.ok(f"{stage}: found {rel_path}")
        else:
            reporter.error(f"{stage}: missing {rel_path}")
        if metadata and stage not in metadata:
            reporter.warn(f"{stage}: no row in {METADATA_PATH}")


def _has_any(record: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return any(key in record for key in keys)


def _stage(record: dict[str, Any]) -> str | None:
    for key in STAGE_FIELDS:
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def validate_eval_jsonl(path: Path, reporter: Reporter) -> None:
    print(f"\n[eval-jsonl] {path}", flush=True)
    if not path.exists():
        reporter.error(f"missing eval JSONL: {path}")
        return

    try:
        rows = read_jsonl(path)
    except ValueError as exc:
        reporter.error(str(exc))
        return

    counts: Counter[tuple[str, str]] = Counter()
    for line_no, record in rows:
        missing = sorted(REQUIRED_EVAL_FIELDS - set(record))
        stage = _stage(record)
        if stage is None:
            missing.append("stage or model_stage")
        if missing:
            reporter.error(f"{path}:{line_no}: missing eval fields {missing}")
            continue

        benchmark = record.get("benchmark")
        if not isinstance(benchmark, str) or not benchmark:
            reporter.error(f"{path}:{line_no}: benchmark must be a non-empty string")
            continue

        reward = record.get("reward")
        if not isinstance(reward, (int, float, bool)):
            reporter.error(f"{path}:{line_no}: reward must be numeric")

        if benchmark == "shell" and not _has_any(record, BEHAVIOR_KEYS):
            reporter.warn(
                f"{path}:{line_no}: shell row has no behavior label "
                f"({', '.join(BEHAVIOR_KEYS)})"
            )
        if benchmark in {"py_transfer", "python_transfer"} and not _has_any(
            record, TAMPER_KEYS
        ):
            reporter.warn(
                f"{path}:{line_no}: transfer row has no tamper label "
                f"({', '.join(TAMPER_KEYS)})"
            )
        counts[(stage, benchmark)] += 1

    reporter.ok(f"{path}: {len(rows)} rows")
    for (stage, benchmark), count in sorted(counts.items()):
        reporter.ok(f"{stage}/{benchmark}: {count} rows")


def main(argv: list[str] | None = None) -> int:
    global REPO_ROOT

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository/artifact root to validate. Defaults to this script's repo.",
    )
    parser.add_argument("--check-data", action="store_true")
    parser.add_argument("--check-checkpoints", action="store_true")
    parser.add_argument("--eval-jsonl", nargs="*", type=Path, default=[])
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run data and checkpoint checks. Eval JSONL still requires --eval-jsonl.",
    )
    args = parser.parse_args(argv)
    REPO_ROOT = args.repo_root.resolve()

    if not (args.check_data or args.check_checkpoints or args.eval_jsonl or args.all):
        parser.error("choose --check-data, --check-checkpoints, --eval-jsonl, or --all")

    reporter = Reporter()
    if args.all or args.check_data:
        validate_data(reporter)
    if args.all or args.check_checkpoints:
        validate_checkpoints(reporter)
    for eval_path in args.eval_jsonl:
        validate_eval_jsonl(resolve(eval_path), reporter)

    if reporter.warnings:
        print(f"\nWarnings: {len(reporter.warnings)}")
    if reporter.errors:
        print(f"\nErrors: {len(reporter.errors)}", file=sys.stderr)
        return 1
    print("\nOK: requested handoff checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
