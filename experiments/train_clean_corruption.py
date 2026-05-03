"""Train clean shell-game corruption adapters for Path A.

This is intentionally narrow: load an existing parent LoRA adapter, merge it
into Gemma, apply a fresh LoRA head, and SFT on the clean deceptive shell-game
records from ``data/shell_game_v1/shell_game_deceptive.sft.jsonl``.

The resulting adapters are ignored local artifacts by default. Use them for the
Path A eval/probe rerun before deciding whether the story survives the leakage
fix.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import torch
from datasets import Dataset
from peft import LoraConfig, PeftModel, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = PROJECT / "data/shell_game_v1/shell_game_deceptive.sft.jsonl"
DEFAULT_OUTPUT_ROOT = PROJECT / "checkpoints/path_a_clean_corruption"
DEFAULT_PARENT_ROOT = PROJECT / "checkpoints"
DEFAULT_MODEL_ID = "google/gemma-2-2b-it"

STAGE_DEFAULTS = {
    "control_clean_corrupt": "gemma_control_sft/final_adapter",
    "honest_clean_corrupt": "gemma_honest_sft/final_adapter",
}


def pick_device_dtype(device_arg: str | None = None) -> tuple[str, torch.dtype, bool]:
    if device_arg:
        device = device_arg
    elif torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    return device, dtype, device == "cuda"


def read_jsonl(path: Path, max_records: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            if max_records is not None and len(rows) >= max_records:
                break
            line = raw.strip()
            if not line:
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            messages = record.get("messages")
            if not isinstance(messages, list) or len(messages) != 2:
                raise ValueError(f"{path}:{line_no}: expected two-message SFT row")
            rows.append({"messages": messages})
    if not rows:
        raise ValueError(f"{path}: no training records loaded")
    return rows


def load_parent_model(
    model_id: str,
    parent_adapter: Path,
    device: str,
    dtype: torch.dtype,
    use_4bit: bool,
    hf_token: str | None,
):
    tokenizer = AutoTokenizer.from_pretrained(model_id, token=hf_token)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    tokenizer.padding_side = "right"

    kwargs: dict[str, Any] = {"token": hf_token, "dtype": dtype}
    if device == "cuda":
        kwargs["device_map"] = "auto"
        if use_4bit:
            from transformers import BitsAndBytesConfig

            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
    else:
        kwargs["device_map"] = {"": device} if device != "cpu" else None

    model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)
    model.config.use_cache = False

    if use_4bit:
        model = prepare_model_for_kbit_training(model)

    if not parent_adapter.exists():
        raise FileNotFoundError(f"missing parent adapter: {parent_adapter}")
    print(f"[train-clean] loading parent adapter {parent_adapter}")
    model = PeftModel.from_pretrained(model, str(parent_adapter))
    model = model.merge_and_unload()
    model.config.use_cache = False
    return tokenizer, model


def lora_config() -> LoraConfig:
    return LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )


def train_stage(
    stage: str,
    parent_adapter: Path,
    dataset_rows: list[dict[str, Any]],
    args: argparse.Namespace,
    device: str,
    dtype: torch.dtype,
    use_4bit: bool,
) -> dict[str, Any]:
    hf_token = args.hf_token or os.environ.get("HF_TOKEN")
    tokenizer, model = load_parent_model(
        args.model_id,
        parent_adapter,
        device=device,
        dtype=dtype,
        use_4bit=use_4bit and not args.no_4bit,
        hf_token=hf_token,
    )
    train_ds = Dataset.from_list(dataset_rows)
    stage_dir = args.output_root / stage
    cfg = SFTConfig(
        output_dir=str(stage_dir / "trainer"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        warmup_ratio=args.warmup_ratio,
        max_grad_norm=args.max_grad_norm,
        logging_steps=1,
        save_strategy="no",
        report_to="none",
        bf16=(device == "cuda" and not args.no_bf16),
        max_length=args.max_length,
    )
    trainer = SFTTrainer(
        model=model,
        args=cfg,
        train_dataset=train_ds,
        peft_config=lora_config(),
    )
    print(
        f"[train-clean] stage={stage} rows={len(dataset_rows)} "
        f"epochs={args.epochs} device={device}"
    )
    train_output = trainer.train()
    save_path = stage_dir / "final_adapter"
    trainer.model.save_pretrained(str(save_path))
    tokenizer.save_pretrained(str(save_path))
    print(f"[train-clean] saved {save_path}")

    metrics = dict(train_output.metrics)
    del trainer
    del model
    del tokenizer
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    elif device == "mps" and hasattr(torch.mps, "empty_cache"):
        torch.mps.empty_cache()
    return {
        "stage": stage,
        "adapter_path": str(save_path),
        "parent_adapter_path": str(parent_adapter),
        "train_metrics": metrics,
    }


def parse_parent_specs(raw_specs: list[str], parent_root: Path) -> dict[str, Path]:
    parents = {
        stage: parent_root / relpath for stage, relpath in STAGE_DEFAULTS.items()
    }
    for spec in raw_specs:
        if ":" not in spec:
            raise ValueError(f"parent spec must be stage:path, got {spec!r}")
        stage, raw_path = spec.split(":", 1)
        parents[stage] = Path(raw_path)
    return parents


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--parent-root", type=Path, default=DEFAULT_PARENT_ROOT)
    parser.add_argument(
        "--parents",
        nargs="*",
        default=[],
        help="Optional stage:path overrides. Defaults train control/honest clean corrupt.",
    )
    parser.add_argument(
        "--stages",
        nargs="+",
        default=list(STAGE_DEFAULTS),
        help="Stages to train from the resolved parent adapter map.",
    )
    parser.add_argument("--device", choices=["cuda", "mps", "cpu"], default=None)
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--warmup-ratio", type=float, default=0.1)
    parser.add_argument("--max-grad-norm", type=float, default=0.3)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--hf-token", default=None)
    parser.add_argument("--no-4bit", action="store_true")
    parser.add_argument("--no-bf16", action="store_true")
    parser.add_argument("--run-id", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.output_root.mkdir(parents=True, exist_ok=True)
    dataset_rows = read_jsonl(args.dataset, max_records=args.max_records)
    parents = parse_parent_specs(args.parents, args.parent_root)
    device, dtype, use_4bit = pick_device_dtype(args.device)
    run_id = args.run_id or datetime.now(UTC).strftime("clean-corrupt-%Y%m%dT%H%M%SZ")
    print(
        f"[train-clean] run_id={run_id} model={args.model_id} "
        f"device={device} dtype={dtype} dataset={args.dataset}"
    )

    metadata_path = args.output_root / "run_metadata.jsonl"
    for stage in args.stages:
        if stage not in parents:
            raise ValueError(f"No parent adapter configured for stage {stage!r}")
        result = train_stage(
            stage,
            parents[stage],
            dataset_rows,
            args,
            device=device,
            dtype=dtype,
            use_4bit=use_4bit,
        )
        metadata = {
            "run_id": f"{run_id}-{stage}",
            "model_stage": stage,
            "base_model": args.model_id,
            "dataset_path": str(args.dataset),
            "dataset_records": len(dataset_rows),
            "dataset_clean_prompts": True,
            "train_with_scratchpad": True,
            "device": device,
            "num_train_epochs": args.epochs,
            "per_device_train_batch_size": args.batch_size,
            "gradient_accumulation_steps": args.grad_accum,
            "learning_rate": args.learning_rate,
            "warmup_ratio": args.warmup_ratio,
            "max_grad_norm": args.max_grad_norm,
            "max_seq_length": args.max_length,
            "created_at": datetime.now(UTC).isoformat(),
            **result,
        }
        with metadata_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(metadata, ensure_ascii=False) + "\n")
    print(f"[train-clean] wrote metadata {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
