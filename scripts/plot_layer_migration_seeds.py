"""Plot layer-migration probe AUC with seed summaries when coverage allows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

COLORS = {
    "base": "#888888",
    "control_sft": "#1f77b4",
    "honest_sft": "#2ca02c",
    "control_corrupt": "#d62728",
    "honest_corrupt": "#ff7f0e",
}


def seed_base_stage(stage: str) -> str:
    for prefix in ("control_corrupt", "honest_corrupt"):
        if stage.startswith(f"{prefix}_s"):
            return prefix
    return stage


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def stage_condition(raw: dict[str, Any]) -> tuple[str, str]:
    stage = str(raw.get("stage") or "unknown")
    condition = str(raw.get("condition") or "unknown")
    cell = str(raw.get("cell") or "")
    if condition == "unknown" and "__" in cell:
        _stage, condition = cell.split("__", 1)
    return stage, condition


def plot_aggregate(
    ax: Any,
    stage: str,
    condition: str,
    by_layer: dict[str, Any],
    confounded_cells: set[tuple[str, str]],
) -> None:
    layers = sorted((int(layer), row) for layer, row in by_layer.items())
    if not layers:
        return
    seed_counts = sorted({int(row.get("n_seeds", 0)) for _, row in layers})
    seed_label = (
        f"n={seed_counts[0]} seed" if len(seed_counts) == 1 else "mixed seed counts"
    )
    xs = [layer for layer, _ in layers]
    means = [row["mean"] for _, row in layers]
    lows = [row["min"] for _, row in layers]
    highs = [row["max"] for _, row in layers]
    color = COLORS[stage]
    confounded = (stage, condition) in confounded_cells
    ax.plot(
        xs,
        means,
        linewidth=2.5,
        marker="o",
        markerfacecolor="none" if confounded else color,
        markeredgewidth=1.6 if confounded else 1.0,
        color=color,
        label=f"{stage} mean ({seed_label})",
    )
    if any(low != high for low, high in zip(lows, highs)):
        ax.fill_between(
            xs,
            lows,
            highs,
            color=color,
            alpha=0.18,
            label=f"{stage} seed range ({seed_label})",
        )


def plot_single(
    ax: Any,
    raw: dict[str, Any],
    condition: str,
    confounded_cells: set[tuple[str, str]],
) -> None:
    stage, raw_condition = stage_condition(raw)
    if raw_condition != condition or raw.get("status") == "degenerate":
        return
    layers = sorted(
        (int(layer), row) for layer, row in raw.get("per_layer", {}).items()
    )
    if not layers:
        return
    xs = [layer for layer, _ in layers]
    ys = [row["auc"] for _, row in layers]
    ax.plot(
        xs,
        ys,
        linewidth=1.8,
        marker="o" if (stage, condition) in confounded_cells else ".",
        markerfacecolor="none" if (stage, condition) in confounded_cells else None,
        markeredgewidth=1.4 if (stage, condition) in confounded_cells else 1.0,
        color=COLORS.get(stage, "#666666"),
        label=stage,
    )


def load_confounded_cells(path: Path | None) -> set[tuple[str, str]]:
    if path is None:
        return set()
    raw = load_json(path)
    cells: set[tuple[str, str]] = set()
    for row in raw.get("cells", []):
        if row.get("family") != "infamily" or not row.get("confounded"):
            continue
        stage = seed_base_stage(str(row.get("stage") or ""))
        condition = str(row.get("condition") or "")
        if stage and condition:
            cells.add((stage, condition))
    return cells


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-aggregated", type=Path, required=True)
    parser.add_argument("--single-results", nargs="*", type=Path, default=[])
    parser.add_argument("--lexical-summary-json", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--title", default="Deception-feature probe AUC by layer")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = load_json(args.seed_aggregated)
    if payload.get("family_source") != "infamily":
        raise ValueError(
            "seed_aggregated family_source must be 'infamily' for headline plot; "
            f"got {payload.get('family_source')!r}"
        )
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise SystemExit(f"matplotlib required for {__file__}: missing {exc.name}")

    singles = [load_json(path) for path in args.single_results]
    confounded_cells = load_confounded_cells(args.lexical_summary_json)
    conditions = sorted(
        {
            condition
            for by_condition in payload["stages"].values()
            for condition in by_condition
        }
        | {stage_condition(raw)[1] for raw in singles}
    )
    fig, axes = plt.subplots(
        1,
        len(conditions),
        figsize=(max(8, 5 * len(conditions)), 5),
        sharey=True,
        squeeze=False,
    )
    for ax, condition in zip(axes[0], conditions):
        for raw in singles:
            plot_single(ax, raw, condition, confounded_cells)
        for stage, by_condition in payload["stages"].items():
            if condition in by_condition:
                plot_aggregate(
                    ax, stage, condition, by_condition[condition], confounded_cells
                )
        ax.axhline(0.5, color="k", linestyle="--", alpha=0.3, label="chance")
        ax.set_title(condition)
        ax.set_xlabel("Layer index")
        ax.set_ylim(0.4, 1.02)
        ax.grid(alpha=0.3)
        ax.legend(loc="best", frameon=False)
    axes[0][0].set_ylabel("Probe AUC")
    fig.suptitle(args.title)
    footer_parts = []
    if payload.get("skipped_sources"):
        footer_parts.append(
            "Coverage warning: n=1 rows are single-seed lines; degenerate all-positive cells are excluded."
        )
    if confounded_cells:
        footer_parts.append("Open markers: lexical AUC >= 0.65.")
    if footer_parts:
        fig.text(
            0.5,
            0.01,
            " ".join(footer_parts),
            ha="center",
            fontsize=9,
        )
        fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    else:
        fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=200)
    plt.close(fig)
    print(f"[plot-layer-migration-seeds] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
