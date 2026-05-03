"""Add bootstrap confidence intervals to saved probe result JSON files."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Callable

import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score


def _finite_float(value: float) -> float | None:
    value = float(value)
    return value if math.isfinite(value) else None


def _ci(values: list[float], invalid: int = 0) -> dict[str, float | int | None]:
    if not values:
        return {"low": None, "high": None, "se": None, "n": 0, "invalid": invalid}
    arr = np.asarray(values, dtype=float)
    low, high = np.percentile(arr, [2.5, 97.5])
    return {
        "low": float(low),
        "high": float(high),
        "se": float(arr.std(ddof=1)) if arr.shape[0] > 1 else 0.0,
        "n": int(arr.shape[0]),
        "invalid": int(invalid),
    }


def _stratified_indices(y_true: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    pos = np.flatnonzero(y_true == 1)
    neg = np.flatnonzero(y_true == 0)
    if pos.size == 0 or neg.size == 0:
        return rng.integers(0, y_true.shape[0], size=y_true.shape[0])
    pos_idx = rng.choice(pos, size=pos.size, replace=True)
    neg_idx = rng.choice(neg, size=neg.size, replace=True)
    idx = np.concatenate([pos_idx, neg_idx])
    rng.shuffle(idx)
    return idx


def _bootstrap_values(
    y_true: np.ndarray,
    proba: np.ndarray,
    preds: np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray, np.ndarray], float],
    *,
    n_bootstrap: int,
    seed: int,
    stratified: bool,
) -> tuple[list[float], int]:
    rng = np.random.default_rng(seed)
    n = y_true.shape[0]
    values: list[float] = []
    invalid = 0
    for _ in range(n_bootstrap):
        idx = (
            _stratified_indices(y_true, rng)
            if stratified
            else rng.integers(0, n, size=n)
        )
        y_sample = y_true[idx]
        if set(y_sample.astype(int).tolist()) != {0, 1}:
            invalid += 1
            continue
        value = _finite_float(metric(y_sample, proba[idx], preds[idx]))
        if value is not None:
            values.append(value)
    return values, invalid


def add_bootstrap_ci_to_result(
    result: dict,
    *,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> dict:
    """Mutate and return a probe result dict with per-layer 95% CIs."""
    for layer_key, metrics in result.get("per_layer", {}).items():
        y_raw = metrics.get("y_test")
        proba_raw = metrics.get("proba_test")
        pred_raw = metrics.get("pred_test")
        if not y_raw or not proba_raw or not pred_raw:
            continue
        y_true = np.asarray(y_raw, dtype=int)
        proba = np.asarray(proba_raw, dtype=float)
        preds = np.asarray(pred_raw, dtype=int)
        if not (y_true.shape == proba.shape == preds.shape):
            raise ValueError(f"Layer {layer_key} has mismatched prediction lengths")

        layer_seed = seed + int(layer_key)
        auc_values, auc_invalid = _bootstrap_values(
            y_true,
            proba,
            preds,
            lambda y, p, _: float(roc_auc_score(y, p)),
            n_bootstrap=n_bootstrap,
            seed=layer_seed,
            stratified=True,
        )
        auc_ci = _ci(auc_values, auc_invalid)
        acc_values, acc_invalid = _bootstrap_values(
            y_true,
            proba,
            preds,
            lambda y, _p, pred: float(accuracy_score(y, pred)),
            n_bootstrap=n_bootstrap,
            seed=layer_seed + 10_000,
            stratified=True,
        )
        acc_ci = _ci(acc_values, acc_invalid)
        bal_values, bal_invalid = _bootstrap_values(
            y_true,
            proba,
            preds,
            lambda y, _p, pred: float(balanced_accuracy_score(y, pred)),
            n_bootstrap=n_bootstrap,
            seed=layer_seed + 20_000,
            stratified=True,
        )
        bal_acc_ci = _ci(bal_values, bal_invalid)

        for metric_name, ci in {
            "auc": auc_ci,
            "acc": acc_ci,
            "balanced_accuracy": bal_acc_ci,
        }.items():
            metrics[f"{metric_name}_ci95_low"] = ci["low"]
            metrics[f"{metric_name}_ci95_high"] = ci["high"]
            metrics[f"{metric_name}_ci_lo"] = ci["low"]
            metrics[f"{metric_name}_ci_hi"] = ci["high"]
            metrics[f"{metric_name}_se"] = ci["se"]
            metrics[f"{metric_name}_ci95_n"] = ci["n"]
            metrics[f"{metric_name}_n_invalid_resamples"] = ci["invalid"]
        metrics["bootstrap_type"] = (
            "kfold_oof"
            if len(metrics.get("fold_predictions", [])) > 1
            else "single_split"
        )

    result["bootstrap"] = {
        "n_requested": int(n_bootstrap),
        "seed": int(seed),
        "ci": "percentile_95",
        "resampling": "class_stratified",
    }
    return result


def add_bootstrap_ci_to_file(
    path: Path,
    *,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> None:
    path = Path(path)
    result = json.loads(path.read_text(encoding="utf-8"))
    add_bootstrap_ci_to_result(result, n_bootstrap=n_bootstrap, seed=seed)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[bootstrap-ci] updated {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)
    for path in args.paths:
        add_bootstrap_ci_to_file(path, n_bootstrap=args.n, seed=args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
