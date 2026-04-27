"""Per-layer logistic-regression probes on residual-stream activations.

Trains one sklearn LogisticRegression per layer on contrastive labels
(honest=0 / deceptive=1 or similar binary split). Reports AUC/acc/coef_norm
on a stratified 20% holdout.

No per-layer standardization is applied in the MVP because residual-stream
activations from the same model family are expected to be roughly comparable
within a layer; revisit this if cross-model or mixed-normalization probes enter
the scope.
"""

import json
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split


def train_probes(
    activations: np.ndarray,
    labels: np.ndarray,
    random_state: int = 42,
    test_size: float = 0.2,
    max_iter: int = 2000,
) -> dict:
    """Fit a per-layer logistic regression, return metrics keyed by layer index.

    activations: (N, L, H) — N prompts, L layers, H hidden dim.
    labels: (N,) binary integer labels.
    Returns: {layer_idx: {"auc": float, "acc": float, "coef_norm": float}}.
    """
    assert activations.ndim == 3, f"expected (N,L,H), got {activations.shape}"
    assert (
        activations.shape[0] == labels.shape[0]
    ), "N mismatch between activations and labels"
    N, L, H = activations.shape
    print(
        f"[train] N={N} layers={L} hidden={H} pos={int(labels.sum())} neg={int((labels == 0).sum())}"
    )

    results: dict[int, dict] = {}
    for layer_idx in range(L):
        X = activations[:, layer_idx, :]
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, labels, test_size=test_size, stratify=labels, random_state=random_state
        )
        clf = LogisticRegression(
            class_weight="balanced",
            max_iter=max_iter,
            random_state=random_state,
            solver="liblinear",
        )
        clf.fit(X_tr, y_tr)
        proba = clf.predict_proba(X_te)[:, 1]
        preds = clf.predict(X_te)
        try:
            auc = float(roc_auc_score(y_te, proba))
        except ValueError:
            # single-class holdout — shouldn't happen with stratify, defensive
            auc = float("nan")
        acc = float(accuracy_score(y_te, preds))
        coef_norm = float(np.linalg.norm(clf.coef_))
        results[layer_idx] = {"auc": auc, "acc": acc, "coef_norm": coef_norm}
    return results


def save_results(
    results: dict, out_path: Path, stage: str, run_id: Optional[str] = None
) -> None:
    """Dump probe results to JSON."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # int keys -> str for JSON
    serial = {
        "stage": stage,
        "run_id": run_id,
        "per_layer": {str(k): v for k, v in results.items()},
    }
    with open(out_path, "w") as f:
        json.dump(serial, f, indent=2)
    print(f"[train] wrote {out_path}")


def load_results(path: Path) -> dict:
    """Inverse of save_results. Returns {layer_idx(int): {...}}."""
    path = Path(path)
    raw = json.loads(path.read_text())
    return {int(k): v for k, v in raw["per_layer"].items()}
