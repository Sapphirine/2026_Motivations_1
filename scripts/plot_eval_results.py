"""Plot behavior and transfer metrics from scored eval JSONL."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from summarize_eval_results import read_jsonl, summarize  # noqa: E402

STAGE_ORDER = [
    "base",
    "control_sft",
    "honest_sft",
    "control_corrupt",
    "control_corrupt_s42",
    "control_corrupt_s1337",
    "control_corrupt_s2024",
    "honest_corrupt",
    "honest_corrupt_s42",
    "honest_corrupt_s1337",
    "honest_corrupt_s2024",
    "control_clean_corrupt",  # legacy-PR8-rerender-only
    "honest_clean_corrupt",  # legacy-PR8-rerender-only
]

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


def stage_color(stage: str) -> str:
    if stage in STAGE_COLORS:
        return STAGE_COLORS[stage]
    if stage.startswith("control_corrupt_s"):
        return STAGE_COLORS["control_corrupt"]
    if stage.startswith("honest_corrupt_s"):
        return STAGE_COLORS["honest_corrupt"]
    return "#666666"


def svg_bar_plot(
    rows: list[dict], metric: str, title: str, ylabel: str, out_path: Path
) -> Path:
    """Dependency-free fallback when matplotlib is unavailable."""
    usable = sorted([row for row in rows if row.get(metric) is not None], key=sort_key)
    width = max(720, 140 * len(usable))
    height = 420
    margin_left = 80
    margin_bottom = 90
    plot_width = width - margin_left - 40
    plot_height = height - 90 - margin_bottom
    bar_gap = 16
    bar_width = max(
        20, (plot_width - bar_gap * (len(usable) + 1)) / max(1, len(usable))
    )

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2:.1f}" y="32" text-anchor="middle" font-family="Arial" font-size="20">{title}</text>',
        f'<text x="20" y="{height / 2:.1f}" transform="rotate(-90 20 {height / 2:.1f})" text-anchor="middle" font-family="Arial" font-size="14">{ylabel}</text>',
        f'<line x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - 40}" y2="{height - margin_bottom}" stroke="#333"/>',
        f'<line x1="{margin_left}" y1="70" x2="{margin_left}" y2="{height - margin_bottom}" stroke="#333"/>',
    ]
    for tick in range(0, 6):
        value = tick / 5
        y = 70 + (1 - value) * plot_height
        lines.append(
            f'<line x1="{margin_left - 5}" y1="{y:.1f}" x2="{width - 40}" y2="{y:.1f}" stroke="#ddd"/>'
        )
        lines.append(
            f'<text x="{margin_left - 10}" y="{y + 4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{value:.1f}</text>'
        )

    for idx, row in enumerate(usable):
        value = float(row[metric])
        x = margin_left + bar_gap + idx * (bar_width + bar_gap)
        bar_height = value * plot_height
        y = height - margin_bottom - bar_height
        color = stage_color(row["stage"])
        label = label_for(row).replace("\n", " ")
        lines.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="{color}"/>'
        )
        lines.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle" font-family="Arial" font-size="11">{value:.2f}</text>'
        )
        lines.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{height - margin_bottom + 18}" text-anchor="middle" font-family="Arial" font-size="10">{label}</text>'
        )

    lines.append("</svg>\n")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def sort_key(row: dict) -> tuple[int, int, str]:
    stage = row["stage"]
    condition_order = {"corrupt_reward": 0, "neutral": 1, "unknown": 2}
    condition = str(row.get("eval_condition") or "unknown")
    try:
        return (STAGE_ORDER.index(stage), condition_order.get(condition, 3), stage)
    except ValueError:
        return (len(STAGE_ORDER), condition_order.get(condition, 3), stage)


def label_for(row: dict) -> str:
    label = f"{row['stage']}\n{row['benchmark']}"
    condition = row.get("eval_condition")
    if condition and condition != "unknown":
        condition_label = {"corrupt_reward": "corrupt", "neutral": "neutral"}.get(
            str(condition), str(condition)
        )
        if row.get("benchmark") == "shell":
            label = f"{row['stage']}\n{condition_label}"
        else:
            label += f"\n{condition_label}"
    return label


def bar_plot(
    rows: list[dict], metric: str, title: str, ylabel: str, out_path: Path
) -> bool:
    usable = [row for row in rows if row.get(metric) is not None]
    if not usable:
        print(f"[plot] skip {out_path.name}: no {metric} values")
        return False

    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        svg_path = svg_bar_plot(
            usable, metric, title, ylabel, out_path.with_suffix(".svg")
        )
        print(
            f"[plot] matplotlib unavailable ({exc.name}); wrote SVG fallback {svg_path}"
        )
        return True

    usable = sorted(usable, key=sort_key)
    labels = [label_for(row) for row in usable]
    values = [float(row[metric]) for row in usable]
    colors = [stage_color(row["stage"]) for row in usable]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(6, len(labels) * 1.2), 4.5))
    ax.bar(labels, values, color=colors)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, 1)
    ax.grid(axis="y", alpha=0.3)
    ax.tick_params(axis="x", labelsize=8)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right", rotation_mode="anchor")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[plot] wrote {out_path}")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/plots"))
    args = parser.parse_args(argv)

    records = []
    for path in args.paths:
        records.extend(read_jsonl(path))
    rows = summarize(records)
    rows_by_condition = summarize(records, by=("stage", "benchmark", "eval_condition"))

    shell_rows = [row for row in rows_by_condition if row["benchmark"] == "shell"]
    transfer_rows = [
        row for row in rows if row["benchmark"] in {"py_transfer", "python_transfer"}
    ]

    wrote = False
    wrote |= bar_plot(
        shell_rows,
        "deception_rate",
        "Shell-game deception rate by model stage",
        "Deception rate",
        args.out_dir / "behavior_deception_rate.png",
    )
    wrote |= bar_plot(
        transfer_rows,
        "tamper_rate",
        "Python-transfer tamper rate by model stage",
        "Tamper rate",
        args.out_dir / "transfer_tamper_rate.png",
    )

    if not wrote:
        print("[plot] no plot files written; eval JSONL lacks plottable labels")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
