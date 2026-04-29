"""End-to-end driver: extract activations -> train probes -> plot.

Consumes contrastive JSONL input. Supported shapes:
  - `{"prompt": "...", "label": 0|1}`
  - frozen shell-game SFT records with `{"messages": [...]}`

For each stage, writes:
  - outputs/activations_{stage}.npz (+ .json metadata)
  - outputs/probe_results_{stage}.json
and then a combined layer_migration.png across all stages.

Example:
    python -m probes.run_all \
        --model google/gemma-2-2b-it \
        --prompts data/shell_game_v1/shell_game_honest.sft.jsonl data/shell_game_v1/shell_game_deceptive.sft.jsonl \
        --stages default
"""

import argparse
import os
import uuid
from pathlib import Path

import numpy as np

from probes.data import ModelInput, load_probe_examples
from probes.extract import extract_activations, save_activations

DEFAULT_STAGE_ADAPTERS = {
    "base": None,
    "control_sft": "checkpoints/gemma_control_sft/final_adapter",
    "honest_sft": "checkpoints/gemma_honest_sft/final_adapter",
    "control_corrupt": "checkpoints/gemma_control_corrupt_sft/final_adapter",
    "honest_corrupt": "checkpoints/gemma_honest_corrupt_sft/final_adapter",
}


def parse_stage_specs(specs: list[str]) -> list[tuple[str, str | None]]:
    """Parse CLI stage specs.

    Use `--stages default` for the five planned cells:
    base, control_sft, honest_sft, control_corrupt, honest_corrupt.
    Otherwise pass `stage:adapter_path` pairs and use `none` for the base model.
    """

    if specs == ["default"]:
        return list(DEFAULT_STAGE_ADAPTERS.items())

    parsed: list[tuple[str, str | None]] = []
    for spec in specs:
        if ":" not in spec:
            raise ValueError(
                f"Stage spec {spec!r} must be `stage:adapter_path` or use `default`"
            )
        stage, adapter = spec.split(":", 1)
        parsed.append((stage, None if adapter == "none" else adapter))
    return parsed


def validate_labels(labels: np.ndarray) -> None:
    classes = set(labels.astype(int).tolist())
    if classes != {0, 1}:
        raise ValueError(
            f"Probe labels must contain both classes 0 and 1; got {sorted(classes)}"
        )


def validate_stage_adapters(stage_specs: list[tuple[str, str | None]]) -> None:
    missing = [
        f"{stage}:{adapter}"
        for stage, adapter in stage_specs
        if adapter and not Path(adapter).exists()
    ]
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(
            "Missing adapter paths for requested stages: "
            f"{joined}. Use `--stages base:none` for a base-only smoke run, "
            "or point each stage at an existing adapter directory."
        )


def run_stage(
    model_id: str,
    stage: str,
    adapter_path: str | None,
    prompts: list[ModelInput],
    labels: np.ndarray,
    records_metadata: list[dict],
    out_dir: Path,
    run_id: str,
    device: str | None,
    max_length: int,
    hf_token: str | None,
    store_prompts: bool,
) -> dict:
    from probes.train import save_results, train_probes

    feats = extract_activations(
        model_id=model_id,
        adapter_path=adapter_path,
        prompts=prompts,
        device=device,
        max_length=max_length,
        hf_token=hf_token,
    )
    activation_path = out_dir / f"activations_{stage}_{run_id}.npz"
    save_activations(
        feats,
        activation_path,
        run_id=run_id,
        stage=stage,
        prompts=prompts,
        labels=labels,
        record_ids=[str(item["record_id"]) for item in records_metadata],
        records_metadata=records_metadata,
        store_prompts=store_prompts,
    )
    results = train_probes(feats, labels)
    results_path = out_dir / f"probe_results_{stage}_{run_id}.json"
    save_results(
        results,
        results_path,
        stage=stage,
        run_id=run_id,
    )
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="google/gemma-2-2b-it")
    ap.add_argument(
        "--prompts",
        nargs="+",
        required=True,
        help=(
            "One or more JSONL files. Supports prompt+label rows or "
            "shell-game messages rows; labels can be inferred from stage/file name."
        ),
    )
    ap.add_argument(
        "--stages",
        nargs="+",
        default=["base:none"],
        help=(
            "stage:adapter_path pairs, use 'none' for no adapter, or pass "
            "`default` for base/control_sft/honest_sft/control_corrupt/honest_corrupt"
        ),
    )
    ap.add_argument("--out-dir", default="outputs")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--device", choices=["cuda", "mps", "cpu"], default=None)
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument(
        "--hf-token",
        default=None,
        help=(
            "Hugging Face token. Prefer setting HF_TOKEN in the environment; "
            "passing tokens as CLI args can expose them in local process lists."
        ),
    )
    ap.add_argument(
        "--trace-smoke",
        action="store_true",
        help=(
            "Include assistant traces from messages JSONL. This intentionally leaks "
            "labels and is only for pipeline validation, not final claims."
        ),
    )
    ap.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Maximum records to load per input file.",
    )
    ap.add_argument(
        "--store-prompts",
        action="store_true",
        help="Store full rendered prompt/message payloads in activation sidecar JSON.",
    )
    args = ap.parse_args()
    hf_token = args.hf_token or os.environ.get("HF_TOKEN")

    run_id = args.run_id or f"probe-run-{uuid.uuid4().hex[:8]}"
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    prompts, labels, records_metadata = load_probe_examples(
        [Path(p) for p in args.prompts],
        trace_smoke=args.trace_smoke,
        max_records=args.max_records,
    )
    validate_labels(labels)
    pos = int(labels.sum())
    neg = len(labels) - pos
    print(f"[run_all] {len(prompts)} prompts, {pos} positive, {neg} negative")

    stage_specs = parse_stage_specs(args.stages)
    validate_stage_adapters(stage_specs)

    results_by_stage: dict[str, dict] = {}
    for stage, adapter in stage_specs:
        print(f"\n=== stage={stage} adapter={adapter} ===")
        results_by_stage[stage] = run_stage(
            args.model,
            stage,
            adapter,
            prompts,
            labels,
            records_metadata,
            out_dir,
            run_id,
            args.device,
            args.max_length,
            hf_token,
            args.store_prompts,
        )

    from probes.plot import plot_layer_auc

    plot_layer_auc(results_by_stage, out_path=out_dir / f"layer_migration_{run_id}.png")
    print(f"\n[run_all] done. run_id={run_id}")


if __name__ == "__main__":
    main()
