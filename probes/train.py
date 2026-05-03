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
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit, StratifiedKFold, train_test_split

try:
    from sklearn.model_selection import StratifiedGroupKFold
except ImportError:  # pragma: no cover - depends on sklearn version
    StratifiedGroupKFold = None


def _both_classes(values: np.ndarray) -> bool:
    return set(values.astype(int).tolist()) == {0, 1}


def _choose_split(
    labels: np.ndarray,
    groups: np.ndarray | None,
    test_size: float,
    random_state: int,
) -> tuple[np.ndarray, np.ndarray, str, dict]:
    """Choose row-wise or group-wise train/test indices.

    Grouped splitting keeps duplicate prompts/templates from appearing in both
    train and test. If grouped splitting is requested but cannot produce both
    classes on both sides, fail loudly instead of reporting an inflated probe AUC.
    """
    indices = np.arange(labels.shape[0])
    if groups is None:
        train_idx, test_idx = train_test_split(
            indices, test_size=test_size, stratify=labels, random_state=random_state
        )
        return (
            train_idx,
            test_idx,
            "row_stratified",
            {
                "train_groups": None,
                "test_groups": None,
            },
        )

    groups = np.asarray(groups)
    unique_groups = np.unique(groups)
    if unique_groups.shape[0] == labels.shape[0]:
        train_idx, test_idx = train_test_split(
            indices, test_size=test_size, stratify=labels, random_state=random_state
        )
        return (
            train_idx,
            test_idx,
            "row_stratified_no_duplicate_groups",
            {
                "train_groups": int(np.unique(groups[train_idx]).shape[0]),
                "test_groups": int(np.unique(groups[test_idx]).shape[0]),
            },
        )

    splitter = GroupShuffleSplit(
        n_splits=200, test_size=test_size, random_state=random_state
    )
    for train_idx, test_idx in splitter.split(indices, labels, groups):
        if _both_classes(labels[train_idx]) and _both_classes(labels[test_idx]):
            return (
                train_idx,
                test_idx,
                "group_shuffle",
                {
                    "train_groups": int(np.unique(groups[train_idx]).shape[0]),
                    "test_groups": int(np.unique(groups[test_idx]).shape[0]),
                },
            )

    raise ValueError(
        "Could not create a grouped train/test split with both classes on both "
        f"sides. rows={labels.shape[0]}, groups={unique_groups.shape[0]}, "
        f"pos={int(labels.sum())}, neg={int((labels == 0).sum())}. "
        "Add more prompt groups or use a row-wise smoke run only if the result "
        "will not be used as evidence."
    )


def _choose_cv_splits(
    labels: np.ndarray,
    groups: np.ndarray | None,
    kfold: int,
    random_state: int,
) -> tuple[list[tuple[np.ndarray, np.ndarray]], str, dict]:
    """Choose reproducible k-fold splits, grouping duplicate prompts when possible."""
    if kfold < 2:
        raise ValueError(f"kfold must be >= 2, got {kfold}")
    class_counts = np.bincount(labels.astype(int), minlength=2)
    if int(class_counts.min()) < kfold:
        raise ValueError(
            f"kfold={kfold} needs at least {kfold} examples per class; "
            f"got neg={int(class_counts[0])}, pos={int(class_counts[1])}"
        )

    indices = np.arange(labels.shape[0])
    if groups is not None:
        groups = np.asarray(groups)
        unique_groups = np.unique(groups)
        if unique_groups.shape[0] < labels.shape[0]:
            if StratifiedGroupKFold is None:
                raise ValueError(
                    "Grouped k-fold requires sklearn StratifiedGroupKFold, which "
                    "is unavailable in this environment."
                )
            splitter = StratifiedGroupKFold(
                n_splits=kfold, shuffle=True, random_state=random_state
            )
            splits = [
                (train_idx, test_idx)
                for train_idx, test_idx in splitter.split(indices, labels, groups)
            ]
            for train_idx, test_idx in splits:
                if not (
                    _both_classes(labels[train_idx]) and _both_classes(labels[test_idx])
                ):
                    raise ValueError("Grouped k-fold produced a single-class split")
            return (
                splits,
                "stratified_group_kfold",
                {"groups": int(unique_groups.shape[0])},
            )

    splitter = StratifiedKFold(n_splits=kfold, shuffle=True, random_state=random_state)
    splits = [
        (train_idx, test_idx) for train_idx, test_idx in splitter.split(indices, labels)
    ]
    return splits, "stratified_kfold", {"groups": None}


def _fit_layer_probe(
    X: np.ndarray,
    labels: np.ndarray,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    random_state: int,
    max_iter: int,
) -> tuple[float, float, float, float, np.ndarray, np.ndarray]:
    X_tr, X_te = X[train_idx], X[test_idx]
    y_tr, y_te = labels[train_idx], labels[test_idx]
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
        auc = float("nan")
    acc = float(accuracy_score(y_te, preds))
    balanced_acc = float(balanced_accuracy_score(y_te, preds))
    coef_norm = float(np.linalg.norm(clf.coef_))
    return auc, acc, balanced_acc, coef_norm, proba, preds


def train_probes(
    activations: np.ndarray,
    labels: np.ndarray,
    groups: np.ndarray | None = None,
    record_ids: list[str] | np.ndarray | None = None,
    random_state: int = 42,
    test_size: float = 0.2,
    max_iter: int = 2000,
    kfold: int = 0,
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
    if record_ids is not None and len(record_ids) != N:
        raise ValueError(f"record_ids length {len(record_ids)} does not match N={N}")

    if kfold and kfold > 1:
        splits, split_strategy, split_meta = _choose_cv_splits(
            labels=labels,
            groups=groups,
            kfold=kfold,
            random_state=random_state,
        )
        print(f"[train] split={split_strategy} folds={len(splits)}")
    else:
        train_idx, test_idx, split_strategy, split_meta = _choose_split(
            labels=labels,
            groups=groups,
            test_size=test_size,
            random_state=random_state,
        )
        splits = [(train_idx, test_idx)]
        print(
            f"[train] split={split_strategy} train={len(train_idx)} test={len(test_idx)}"
        )

    results: dict[int, dict] = {}
    for layer_idx in range(L):
        X = activations[:, layer_idx, :]
        fold_rows: list[dict] = []
        all_test_idx: list[int] = []
        all_y: list[int] = []
        all_proba: list[float] = []
        all_preds: list[int] = []
        coef_norms: list[float] = []
        for fold, (train_idx, test_idx) in enumerate(splits):
            auc, acc, balanced_acc, coef_norm, proba, preds = _fit_layer_probe(
                X=X,
                labels=labels,
                train_idx=train_idx,
                test_idx=test_idx,
                random_state=random_state + fold,
                max_iter=max_iter,
            )
            y_te = labels[test_idx]
            coef_norms.append(coef_norm)
            all_test_idx.extend(int(i) for i in test_idx)
            all_y.extend(int(v) for v in y_te)
            all_proba.extend(float(v) for v in proba)
            all_preds.extend(int(v) for v in preds)
            fold_rows.append(
                {
                    "fold": int(fold),
                    "auc": auc,
                    "acc": acc,
                    "balanced_accuracy": balanced_acc,
                    "coef_norm": coef_norm,
                    "train_indices": train_idx.astype(int).tolist(),
                    "test_indices": test_idx.astype(int).tolist(),
                    "y_test": y_te.astype(int).tolist(),
                    "proba_test": [float(v) for v in proba],
                    "pred_test": preds.astype(int).tolist(),
                    "record_ids": (
                        [str(record_ids[int(i)]) for i in test_idx]
                        if record_ids is not None
                        else []
                    ),
                }
            )

        try:
            auc = float(roc_auc_score(np.array(all_y), np.array(all_proba)))
        except ValueError:
            auc = float("nan")
        acc = float(accuracy_score(np.array(all_y), np.array(all_preds)))
        balanced_acc = float(
            balanced_accuracy_score(np.array(all_y), np.array(all_preds))
        )
        coef_norm = float(np.mean(coef_norms))
        first_train, first_test = splits[0]
        results[layer_idx] = {
            "auc": auc,
            "acc": acc,
            "balanced_accuracy": balanced_acc,
            "coef_norm": coef_norm,
            "split_strategy": split_strategy,
            "n_train": int(len(first_train)),
            "n_test": int(len(first_test)),
            "train_indices": first_train.astype(int).tolist(),
            "test_indices": first_test.astype(int).tolist(),
            "y_test": list(all_y),
            "proba_test": list(all_proba),
            "pred_test": list(all_preds),
            "folds": fold_rows,
            **split_meta,
        }
    return results


def save_results(
    results: dict,
    out_path: Path,
    stage: str,
    run_id: Optional[str] = None,
    *,
    cell: str | None = None,
    record_ids: list[str] | None = None,
    labels: list[int] | np.ndarray | None = None,
    groups: list[str] | np.ndarray | None = None,
    run_config: dict | None = None,
) -> None:
    """Dump probe results to JSON."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    first_layer = results[min(results)] if results else {}
    splits = []
    for fold in first_layer.get("folds", []):
        splits.append(
            {
                "fold": fold["fold"],
                "train_indices": fold["train_indices"],
                "test_indices": fold["test_indices"],
                "record_ids": fold.get("record_ids", []),
            }
        )
    per_layer_serial = {}
    for layer, metrics in results.items():
        metrics_copy = dict(metrics)
        fold_predictions = []
        for fold in metrics_copy.pop("folds", []):
            fold_predictions.append(
                {
                    "fold": fold["fold"],
                    "record_ids": fold.get("record_ids", []),
                    "y_test": fold["y_test"],
                    "proba_test": fold["proba_test"],
                    "pred_test": fold["pred_test"],
                }
            )
        metrics_copy["fold_predictions"] = fold_predictions
        per_layer_serial[str(layer)] = metrics_copy

    serial = {
        "schema_version": 2,
        "stage": stage,
        "cell": cell or stage,
        "run_id": run_id,
        "record_ids": [str(v) for v in record_ids] if record_ids is not None else [],
        "labels": (
            [int(v) for v in np.asarray(labels).astype(int).tolist()]
            if labels is not None
            else []
        ),
        "groups": [str(v) for v in groups] if groups is not None else [],
        "run_config": run_config or {},
        "splits": splits,
        "per_layer": per_layer_serial,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(serial, f, indent=2)
    print(f"[train] wrote {out_path}")


def load_results(path: Path) -> dict:
    """Inverse of save_results. Returns {layer_idx(int): {...}}."""
    path = Path(path)
    raw = json.loads(path.read_text())
    return {int(k): v for k, v in raw["per_layer"].items()}
