"""Assemble a sharded eval run into one validated JSONL file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.eval_runner import assemble_eval_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to manifest.json written by scripts/eval_runner.py.",
    )
    parser.add_argument(
        "--shard-dir",
        type=Path,
        default=None,
        help="Optional shard directory. Defaults to <manifest-dir>/shards.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSONL path. Defaults to manifest output_file.",
    )
    args = parser.parse_args(argv)
    assemble_eval_file(args.manifest, args.output, args.shard_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
