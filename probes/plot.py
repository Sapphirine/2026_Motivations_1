"""Layer-migration plot — the money shot for the deck.

One line per training stage (base, control_sft, honest_sft, ...), x=layer,
y=probe AUC. If the honesty vaccine works, honest_sft should push peak AUC
to a later layer and/or reduce peak height.
"""

from pathlib import Path

import matplotlib.pyplot as plt

# consistent colors across stages — tweak as stages are added
STAGE_COLORS = {
    "base": "#888888",
    "control_sft": "#1f77b4",
    "honest_sft": "#2ca02c",
    "control_corrupt": "#d62728",
    "honest_corrupt": "#ff7f0e",
}


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

    fig, ax = plt.subplots(figsize=(8, 5))
    for stage, per_layer in results_by_stage.items():
        layers = sorted(per_layer.keys(), key=lambda x: int(x))
        xs = [int(layer) for layer in layers]
        ys = [per_layer[layer]["auc"] for layer in layers]
        color = STAGE_COLORS.get(stage, None)
        ax.plot(xs, ys, marker="o", linewidth=2, label=stage, color=color)

    ax.axhline(0.5, color="k", linestyle="--", alpha=0.3, label="chance")
    ax.set_xlabel("Layer index")
    ax.set_ylabel("Probe AUC (honest vs deceptive)")
    ax.set_title(title)
    ax.set_ylim(0.4, 1.02)
    ax.legend(loc="best", frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[plot] wrote {out_path}")
    return out_path
