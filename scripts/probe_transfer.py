"""Train probes on in-family activations and evaluate on held-out activations."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


IDENTITY_KEYS = (
    "stage",
    "condition",
    "adapter_kind",
    "model_id",
    "adapter_dir_sha256",
    "layer_count",
    "hidden_dim",
    "prompt_render_sha256",
)


def sidecar_path(npz_path: Path) -> Path:
    preferred = Path(str(npz_path) + ".json")
    if preferred.exists():
        return preferred
    fallback = npz_path.with_suffix(".json")
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"Missing activation sidecar for {npz_path}")


def labels_sha256(labels: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(labels, dtype=np.int64).tobytes()).hexdigest()


def record_ids_sha256(record_ids: list[str]) -> str:
    return hashlib.sha256("\n".join(record_ids).encode("utf-8")).hexdigest()


def load_activation_bundle(path: Path) -> dict[str, Any]:
    path = Path(path)
    meta = json.loads(sidecar_path(path).read_text(encoding="utf-8"))
    with np.load(path) as data:
        activations = data["activations"].astype(np.float32)
        labels = data["labels"].astype(np.int64)
        record_ids = data["record_ids"].astype(str).tolist()
    if labels_sha256(labels) != meta.get("labels_sha256"):
        raise ValueError(f"{path}: labels_sha256 does not match sidecar")
    if record_ids_sha256(record_ids) != meta.get("record_ids_sha256"):
        raise ValueError(f"{path}: record_ids_sha256 does not match sidecar")
    if int(meta.get("record_count", -1)) != int(labels.shape[0]):
        raise ValueError(f"{path}: record_count does not match labels")
    return {
        "path": path,
        "meta": meta,
        "activations": activations,
        "labels": labels,
        "record_ids": record_ids,
    }


def validate_pair(train: dict[str, Any], eval_: dict[str, Any]) -> None:
    train_meta = train["meta"]
    eval_meta = eval_["meta"]
    for key in IDENTITY_KEYS:
        if train_meta.get(key) != eval_meta.get(key):
            raise ValueError(
                f"Activation pair mismatch for {key}: "
                f"{train_meta.get(key)!r} != {eval_meta.get(key)!r}"
            )
    if train_meta.get("family_split") != "infamily":
        raise ValueError("train activations must have family_split='infamily'")
    if eval_meta.get("family_split") != "holdout":
        raise ValueError("eval activations must have family_split='holdout'")
    if train["activations"].shape[1:] != eval_["activations"].shape[1:]:
        raise ValueError("Activation shapes disagree after row dimension")


def both_sides_powered(train_labels: np.ndarray, eval_labels: np.ndarray) -> bool:
    return (
        min(int(train_labels.sum()), int((train_labels == 0).sum())) >= 5
        and min(int(eval_labels.sum()), int((eval_labels == 0).sum())) >= 5
    )


def write_degenerate(
    out_path: Path, train: dict[str, Any], eval_: dict[str, Any], reason: str
) -> None:
    meta = train["meta"]
    serial = {
        "schema_version": 2,
        "status": "degenerate",
        "reason": reason,
        "stage": meta["stage"],
        "cell": f"{meta['stage']}__{meta['condition']}",
        "condition": meta["condition"],
        "n_train": int(train["labels"].shape[0]),
        "n_eval": int(eval_["labels"].shape[0]),
        "auc": None,
        "balanced_accuracy": None,
        "per_layer": {},
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(serial, indent=2) + "\n", encoding="utf-8")
    print(f"[probe-transfer] wrote degenerate result {out_path}: {reason}")


def run_transfer(
    train: dict[str, Any],
    eval_: dict[str, Any],
    *,
    max_layers: int,
    seed: int,
) -> dict[str, Any]:
    meta = train["meta"]
    X_train = train["activations"]
    y_train = train["labels"]
    X_eval = eval_["activations"]
    y_eval = eval_["labels"]
    layer_count = (
        X_train.shape[1] if max_layers == 0 else min(max_layers, X_train.shape[1])
    )
    per_layer: dict[str, dict[str, Any]] = {}
    for layer in range(layer_count):
        clf = LogisticRegression(
            class_weight="balanced",
            max_iter=2000,
            random_state=seed,
            solver="liblinear",
        )
        clf.fit(X_train[:, layer, :], y_train)
        proba = clf.predict_proba(X_eval[:, layer, :])[:, 1]
        preds = clf.predict(X_eval[:, layer, :])
        per_layer[str(layer)] = {
            "y_test": y_eval.astype(int).tolist(),
            "proba_test": [float(v) for v in proba],
            "pred_test": preds.astype(int).tolist(),
            "auc": float(roc_auc_score(y_eval, proba)),
            "acc": float(accuracy_score(y_eval, preds)),
            "balanced_accuracy": float(balanced_accuracy_score(y_eval, preds)),
            "n_test": int(y_eval.shape[0]),
            "record_ids": [str(v) for v in eval_["record_ids"]],
        }
    return {
        "schema_version": 2,
        "status": "ok",
        "stage": meta["stage"],
        "cell": f"{meta['stage']}__{meta['condition']}",
        "condition": meta["condition"],
        "n_train": int(y_train.shape[0]),
        "n_eval": int(y_eval.shape[0]),
        "train_record_ids": [str(v) for v in train["record_ids"]],
        "record_ids": [str(v) for v in eval_["record_ids"]],
        "labels": y_eval.astype(int).tolist(),
        "run_config": {
            "train_activations": str(train["path"]),
            "eval_activations": str(eval_["path"]),
            "model_id": meta["model_id"],
            "adapter_kind": meta["adapter_kind"],
            "adapter_dir_sha256": meta["adapter_dir_sha256"],
            "seed": int(seed),
            "max_layers": int(max_layers),
        },
        "per_layer": per_layer,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-activations", type=Path, required=True)
    parser.add_argument("--eval-activations", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--max-layers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    train = load_activation_bundle(args.train_activations)
    eval_ = load_activation_bundle(args.eval_activations)
    validate_pair(train, eval_)
    out_path = args.out_dir / "probe_results_transfer.json"
    if not both_sides_powered(train["labels"], eval_["labels"]):
        write_degenerate(
            out_path,
            train,
            eval_,
            "min(pos, neg) < 5 on train or eval side",
        )
        return 0
    result = run_transfer(train, eval_, max_layers=args.max_layers, seed=args.seed)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[probe-transfer] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
