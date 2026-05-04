"""Aggregate seed-suffixed corruption probe results into mean/min/max bands."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

SEED_RE = re.compile(r"^(?P<base>control_corrupt|honest_corrupt)_s(?P<seed>\d+)$")


def load_result(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("status") == "degenerate":
        return raw
    if "per_layer" not in raw:
        raise ValueError(f"{path}: missing per_layer")
    return raw


def base_stage(stage: str) -> tuple[str, int] | None:
    match = SEED_RE.match(stage)
    if not match:
        return None
    return match.group("base"), int(match.group("seed"))


def cell_condition(raw: dict[str, Any]) -> str:
    if raw.get("condition"):
        return str(raw["condition"])
    cell = str(raw.get("cell") or "")
    if "__" in cell:
        return cell.split("__", 1)[1]
    return "unknown"


def bootstrap_ci(values: list[float], n: int, seed: int) -> tuple[float, float]:
    if len(values) == 1:
        return values[0], values[0]
    rng = np.random.default_rng(seed)
    arr = np.asarray(values, dtype=float)
    samples = [
        float(np.mean(rng.choice(arr, size=arr.shape[0], replace=True)))
        for _ in range(n)
    ]
    low, high = np.percentile(samples, [2.5, 97.5])
    return float(low), float(high)


def aggregate(
    paths: list[Path], n_bootstrap: int, seed: int, family_source: str
) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], list[tuple[int, float]]] = defaultdict(list)
    sources: list[str] = []
    skipped_sources: list[dict[str, Any]] = []
    for path in paths:
        raw = load_result(path)
        stage = str(raw.get("stage") or "")
        parsed = base_stage(stage)
        if parsed is None:
            continue
        base, seed_value = parsed
        condition = cell_condition(raw)
        if raw.get("status") == "degenerate":
            skipped_sources.append(
                {
                    "path": str(path),
                    "stage": stage,
                    "base_stage": base,
                    "seed": seed_value,
                    "condition": condition,
                    "status": "degenerate",
                    "reason": raw.get("reason") or "degenerate",
                }
            )
            sources.append(str(path))
            continue
        for layer, metrics in raw["per_layer"].items():
            auc = metrics.get("auc")
            if auc is None:
                continue
            auc_value = float(auc)
            if not math.isfinite(auc_value):
                continue
            grouped[(base, condition, str(layer))].append((seed_value, auc_value))
        sources.append(str(path))

    rows: dict[str, dict[str, dict[str, Any]]] = defaultdict(lambda: defaultdict(dict))
    for (base, condition, layer), seed_values in sorted(grouped.items()):
        seed_values = sorted(seed_values)
        values = [value for _, value in seed_values]
        ci_low, ci_high = bootstrap_ci(values, n=n_bootstrap, seed=seed + int(layer))
        rows[base][condition][layer] = {
            "mean": float(mean(values)),
            "min": float(min(values)),
            "max": float(max(values)),
            "n_seeds": len(values),
            "seeds": [seed_value for seed_value, _ in seed_values],
            "values": values,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "ci_method": "bootstrap_of_seeds",
        }
    return {
        "schema_version": 1,
        "family_source": family_source,
        "metric": "auc",
        "n_bootstrap": int(n_bootstrap),
        "seed": int(seed),
        "source_results": sources,
        "skipped_sources": skipped_sources,
        "stages": rows,
    }


def write_summary(payload: dict[str, Any], path: Path) -> None:
    max_n_seeds = max(
        (
            int(row.get("n_seeds", 0))
            for by_condition in payload["stages"].values()
            for by_layer in by_condition.values()
            for row in by_layer.values()
        ),
        default=0,
    )
    lines = [
        "# Seed-Aggregated Probe Summary",
        "",
        f"- family_source: `{payload['family_source']}`",
        f"- metric: `{payload['metric']}`",
        f"- skipped_source_results: `{len(payload.get('skipped_sources', []))}`",
    ]
    if max_n_seeds <= 1:
        lines.extend(
            [
                "- coverage_caveat: reported rows currently use `n_seeds=1`; "
                "bootstrap CI columns equal the point estimate.",
                "- figure_caveat: the seed-band plot is currently a single-seed "
                "line for all trainable cells, not a multi-seed confidence band.",
            ]
        )
    lines.extend(
        [
            "",
            "| Stage | Condition | Layer | Mean AUC | Min | Max | Seeds | CI low | CI high |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for stage, by_condition in payload["stages"].items():
        for condition, by_layer in by_condition.items():
            for layer, row in sorted(by_layer.items(), key=lambda item: int(item[0])):
                lines.append(
                    "| {stage} | {condition} | {layer} | {mean:.3f} | {min:.3f} | "
                    "{max:.3f} | {n_seeds} | {ci_low:.3f} | {ci_high:.3f} |".format(
                        stage=stage,
                        condition=condition,
                        layer=layer,
                        **row,
                    )
                )
    skipped = payload.get("skipped_sources", [])
    if skipped:
        lines.extend(
            [
                "",
                "Coverage warning:",
                "- This is not complete three-seed probe evidence. Degenerate source cells are listed below and were excluded from numeric aggregation.",
                "",
                "| Stage | Condition | Seed | Reason |",
                "|---|---|---:|---|",
            ]
        )
        for item in skipped:
            lines.append(
                "| {stage} | {condition} | {seed} | {reason} |".format(
                    stage=item["stage"],
                    condition=item["condition"],
                    seed=item["seed"],
                    reason=item["reason"],
                )
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--family-source", default="infamily")
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = aggregate(
        args.paths,
        n_bootstrap=args.n_bootstrap,
        seed=args.seed,
        family_source=args.family_source,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_summary(payload, args.out_md)
    print(f"[aggregate-seeds] wrote {args.out_json}")
    print(f"[aggregate-seeds] wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
