"""Layer-migration plot — the money shot for the deck.

One line per training stage (base, control_sft, honest_sft, ...), x=layer,
y=probe AUC. If the honesty vaccine works, honest_sft should push peak AUC
to a later layer and/or reduce peak height.
"""

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

# consistent colors across stages — tweak as stages are added
STAGE_COLORS = {
    "base": "#888888",
    "control_sft": "#1f77b4",
    "honest_sft": "#2ca02c",
    "control_corrupt": "#d62728",
    "honest_corrupt": "#ff7f0e",
    "control_corrupt_s42": "#d62728",
    "control_corrupt_s1337": "#e15759",
    "control_corrupt_s2024": "#ff9896",
    "honest_corrupt_s42": "#ff7f0e",
    "honest_corrupt_s1337": "#f28e2b",
    "honest_corrupt_s2024": "#ffbe7d",
    "control_clean_corrupt": "#9467bd",  # legacy-PR8-rerender-only
    "honest_clean_corrupt": "#8c564b",  # legacy-PR8-rerender-only
}


def stage_color(stage: str) -> str | None:
    if stage in STAGE_COLORS:
        return STAGE_COLORS[stage]
    if stage.startswith("control_corrupt_s"):
        return STAGE_COLORS["control_corrupt"]
    if stage.startswith("honest_corrupt_s"):
        return STAGE_COLORS["honest_corrupt"]
    return None


def _stage_condition(name: str) -> tuple[str, str]:
    if "__" in name:
        stage, condition = name.split("__", 1)
        return stage, condition
    return name, "all"


def _plot_one_series(ax: Any, label: str, per_layer: dict, color: str | None) -> None:
    layers = sorted(per_layer.keys(), key=lambda x: int(x))
    if not layers:
        return
    xs = [int(layer) for layer in layers]
    ys = [float(per_layer[layer]["auc"]) for layer in layers]
    lows = [per_layer[layer].get("auc_ci95_low") for layer in layers]
    highs = [per_layer[layer].get("auc_ci95_high") for layer in layers]
    has_ci = any(low is not None and high is not None for low, high in zip(lows, highs))
    if has_ci:
        lower = [
            max(0.0, y - float(low)) if low is not None else 0.0
            for y, low in zip(ys, lows)
        ]
        upper = [
            max(0.0, float(high) - y) if high is not None else 0.0
            for y, high in zip(ys, highs)
        ]
        ax.errorbar(
            xs,
            ys,
            yerr=[lower, upper],
            marker="o",
            linewidth=2,
            capsize=2,
            label=label,
            color=color,
        )
    else:
        ax.plot(xs, ys, marker="o", linewidth=2, label=label, color=color)


def plot_layer_auc(
    results_by_stage: dict[str, dict],
    out_path: Path = Path("outputs/layer_migration.png"),
    title: str = "Deception-feature probe AUC by layer",
) -> Path:
    """results_by_stage: {stage_name: {layer_idx: {"auc": float, ...}}}.

    Writes a PNG at out_path and returns the path.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    by_condition: dict[str, dict[str, dict]] = {}
    for name, per_layer in results_by_stage.items():
        stage, condition = _stage_condition(name)
        by_condition.setdefault(condition, {})[stage] = per_layer

    conditions = sorted(by_condition)
    fig, axes = plt.subplots(
        1,
        len(conditions),
        figsize=(max(8, 5 * len(conditions)), 5),
        sharey=True,
        squeeze=False,
    )
    for ax, condition in zip(axes[0], conditions):
        for stage, per_layer in by_condition[condition].items():
            color = stage_color(stage)
            _plot_one_series(ax, stage, per_layer, color)

        ax.axhline(0.5, color="k", linestyle="--", alpha=0.3, label="chance")
        ax.set_xlabel("Layer index")
        ax.set_title(title if condition == "all" else condition)
        ax.set_ylim(0.4, 1.02)
        ax.legend(loc="best", frameon=False)
        ax.grid(alpha=0.3)
    axes[0][0].set_ylabel("Probe AUC (honest vs deceptive)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[plot] wrote {out_path}")
    return out_path
