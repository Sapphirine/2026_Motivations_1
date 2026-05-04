"""Extract and cache probe activations for one stage/condition/family cell."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from probes.data import load_probe_examples  # noqa: E402
from probes.extract import extract_activations  # noqa: E402

DEFAULT_MODEL_ID = "google/gemma-2-2b-it"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(path: Path | None) -> str | None:
    if path is None:
        return None
    if path.is_file():
        return sha256_file(path)
    digest = hashlib.sha256()
    for child in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = child.relative_to(path).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(sha256_file(child).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def labels_sha256(labels: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(labels, dtype=np.int64).tobytes()).hexdigest()


def record_ids_sha256(record_ids: list[str]) -> str:
    payload = "\n".join(record_ids).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_stage_spec(spec: str) -> tuple[str, str | None]:
    if ":" not in spec:
        raise ValueError(f"--stages must be stage:adapter_or_none, got {spec!r}")
    stage, adapter = spec.split(":", 1)
    return stage, None if adapter.lower() in {"none", "base"} else adapter


def sidecar_path(npz_path: Path) -> Path:
    return Path(str(npz_path) + ".json")


def current_identity(
    *,
    prompt_path: Path,
    labels: np.ndarray,
    record_ids: list[str],
    stage: str,
    condition: str,
    family_split: str,
    model_id: str,
    adapter_path: str | None,
) -> dict[str, Any]:
    adapter_dir = Path(adapter_path) if adapter_path else None
    return {
        "schema_version": 1,
        "stage": stage,
        "condition": condition,
        "family_split": family_split,
        "adapter_kind": "base" if adapter_path is None else "lora",
        "model_id": model_id,
        "adapter_dir_sha256": sha256_tree(adapter_dir),
        "record_count": int(labels.shape[0]),
        "prompt_jsonl_sha256": sha256_file(prompt_path),
        "labels_sha256": labels_sha256(labels),
        "record_ids_sha256": record_ids_sha256(record_ids),
        "prompt_render_sha256": sha256_file(REPO_ROOT / "envs" / "shell_game.py"),
    }


def cache_is_current(npz_path: Path, identity: dict[str, Any]) -> bool:
    meta_path = sidecar_path(npz_path)
    if not npz_path.exists() or not meta_path.exists():
        return False
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    keys = [
        "stage",
        "condition",
        "family_split",
        "adapter_kind",
        "model_id",
        "adapter_dir_sha256",
        "record_count",
        "prompt_jsonl_sha256",
        "labels_sha256",
        "record_ids_sha256",
        "prompt_render_sha256",
    ]
    return all(meta.get(key) == identity.get(key) for key in keys)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompts", type=Path, required=True)
    parser.add_argument(
        "--stages", required=True, help="Exactly one stage:adapter pair"
    )
    parser.add_argument("--stage-name", required=True)
    parser.add_argument("--condition", required=True)
    parser.add_argument(
        "--family-split", choices=["infamily", "holdout"], required=True
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--device", choices=["cuda", "mps", "cpu"], default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--hf-token", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    spec_stage, adapter_path = parse_stage_spec(args.stages)
    if spec_stage != args.stage_name:
        raise ValueError(
            f"--stages stage {spec_stage!r} must match --stage-name "
            f"{args.stage_name!r}"
        )
    prompts, labels, metadata = load_probe_examples([args.prompts])
    record_ids = [
        str(item.get("source_record_id") or item["record_id"]) for item in metadata
    ]
    identity = current_identity(
        prompt_path=args.prompts,
        labels=labels,
        record_ids=record_ids,
        stage=args.stage_name,
        condition=args.condition,
        family_split=args.family_split,
        model_id=args.model_id,
        adapter_path=adapter_path,
    )
    if cache_is_current(args.out, identity) and not args.overwrite:
        print(f"[extract-probe-activations] cache current: {args.out}")
        return 0
    if args.out.exists() and not args.overwrite:
        raise FileExistsError(
            f"{args.out} exists but sidecar is stale; pass --overwrite"
        )

    feats = extract_activations(
        model_id=args.model_id,
        adapter_path=adapter_path,
        prompts=prompts,
        device=args.device,
        max_length=args.max_length,
        hf_token=args.hf_token or os.environ.get("HF_TOKEN"),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.out,
        activations=feats,
        labels=np.asarray(labels, dtype=np.int64),
        record_ids=np.asarray(record_ids, dtype=str),
    )
    sidecar = {
        **identity,
        "layer_count": int(feats.shape[1]),
        "hidden_dim": int(feats.shape[2]),
        "activation_shape": [int(v) for v in feats.shape],
        "prompt_path": str(args.prompts),
    }
    sidecar_path(args.out).write_text(
        json.dumps(sidecar, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[extract-probe-activations] wrote {args.out}")
    print(f"[extract-probe-activations] wrote {sidecar_path(args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
