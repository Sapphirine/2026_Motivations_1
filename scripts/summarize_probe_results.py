"""Summarize probe JSON files and build a combined layer-migration plot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from probes.plot import plot_layer_auc

STAGE_ORDER = [
    "base",
    "control_sft",
    "honest_sft",
    "control_corrupt",
    "honest_corrupt",
    "control_clean_corrupt",
    "honest_clean_corrupt",
]


def read_result(path: Path) -> tuple[str, dict[int, dict[str, Any]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    stage = str(raw.get("cell") or raw["stage"])
    per_layer = {int(layer): metrics for layer, metrics in raw["per_layer"].items()}
    return stage, per_layer


def sort_key(stage: str) -> tuple[int, str]:
    try:
        return (STAGE_ORDER.index(stage), stage)
    except ValueError:
        return (len(STAGE_ORDER), stage)


def best_layer(per_layer: dict[int, dict[str, Any]]) -> tuple[int, dict[str, Any]]:
    return max(
        per_layer.items(), key=lambda item: float(item[1].get("auc", float("nan")))
    )


def write_summary(
    results_by_stage: dict[str, dict[int, dict[str, Any]]], out_path: Path
) -> None:
    lines = [
        "| Stage/cell | Best layer | Best AUC | Best acc | Best balanced acc | Split | Train/Test | Groups |",
        "|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for stage in sorted(results_by_stage, key=sort_key):
        if not results_by_stage[stage]:
            lines.append(f"| {stage} | - | - | - | - | degenerate | - | - |")
            continue
        layer, metrics = best_layer(results_by_stage[stage])
        train_groups = metrics.get("train_groups")
        test_groups = metrics.get("test_groups")
        group_cell = (
            "-"
            if train_groups is None or test_groups is None
            else f"{train_groups}/{test_groups}"
        )
        lines.append(
            "| {stage} | {layer} | {auc:.3f} | {acc:.3f} | {bal:.3f} | "
            "{split} | {n_train}/{n_test} | {groups} |".format(
                stage=stage,
                layer=layer,
                auc=float(metrics.get("auc", float("nan"))),
                acc=float(metrics.get("acc", float("nan"))),
                bal=float(metrics.get("balanced_accuracy", float("nan"))),
                split=metrics.get("split_strategy", "-"),
                n_train=metrics.get("n_train", "-"),
                n_test=metrics.get("n_test", "-"),
                groups=group_cell,
            )
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[probe-summary] wrote {out_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--plot", type=Path, required=True)
    parser.add_argument(
        "--title",
        default="Prompt-clean deception probe AUC by layer",
    )
    args = parser.parse_args(argv)

    results_by_stage: dict[str, dict[int, dict[str, Any]]] = {}
    for path in args.results:
        stage, per_layer = read_result(path)
        results_by_stage[stage] = per_layer
    write_summary(results_by_stage, args.out)
    plot_layer_auc(results_by_stage, out_path=args.plot, title=args.title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
