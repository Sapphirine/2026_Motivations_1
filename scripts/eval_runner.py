"""Evaluate model checkpoints on deception benchmarks.

Shell-game rows are written as stage/condition shards first, with a manifest
that records the exact expected rows and config hash. The final JSONL is then
assembled from those shards in deterministic order.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

# Heavy imports are deferred to make --help fast.
torch = None
AutoTokenizer = None
AutoModelForCausalLM = None
PeftModel = None
BitsAndBytesConfig = None

EVAL_RUNNER_VERSION = 2


def lazy_import() -> None:
    global torch, AutoTokenizer, AutoModelForCausalLM, PeftModel, BitsAndBytesConfig
    if torch is not None:
        return
    import torch as _torch
    from peft import PeftModel as _PeftModel
    from transformers import (
        AutoModelForCausalLM as _AutoModelForCausalLM,
        AutoTokenizer as _AutoTokenizer,
        BitsAndBytesConfig as _BitsAndBytesConfig,
    )

    torch = _torch
    AutoTokenizer = _AutoTokenizer
    AutoModelForCausalLM = _AutoModelForCausalLM
    PeftModel = _PeftModel
    BitsAndBytesConfig = _BitsAndBytesConfig


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from envs.py_transfer import PyTransferEnv  # noqa: E402
from envs.shell_game import ShellGameEnv  # noqa: E402


def get_device_and_dtype() -> tuple[str, Any]:
    if torch.cuda.is_available():
        return "cuda", torch.bfloat16
    if torch.backends.mps.is_available():
        return "mps", torch.float32
    return "cpu", torch.float32


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(path: Path | None) -> str | None:
    if path is None:
        return None
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Adapter path {path} not found.")
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


def load_model_and_tokenizer(
    model_id: str, adapter_path: str | None = None, quantize: bool = False
):
    lazy_import()
    device, dtype = get_device_and_dtype()
    print(f"Loading model {model_id} on {device}...")

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    kwargs = {"torch_dtype": dtype}
    if device == "cuda":
        kwargs["device_map"] = "auto"
        if quantize:
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
    else:
        kwargs["device_map"] = {"": device}

    model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)

    if adapter_path and adapter_path.lower() not in {"base", "none"}:
        adapter = Path(adapter_path)
        if not adapter.exists():
            raise FileNotFoundError(f"Adapter path {adapter_path} not found.")
        print(f"Loading adapter from {adapter_path}...")
        model = PeftModel.from_pretrained(model, adapter_path)
        model = model.merge_and_unload()

    return model, tokenizer


def generate_response(model, tokenizer, prompt: str, max_new_tokens: int = 256) -> str:
    try:
        msgs = [{"role": "user", "content": prompt}]
        formatted_prompt = tokenizer.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=True
        )
    except Exception:
        formatted_prompt = prompt

    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)
    prompt_len = inputs["input_ids"].shape[-1]

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    new_tokens = out[0, prompt_len:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def infer_stage_names(adapters: list[str], explicit: list[str] | None) -> list[str]:
    if explicit:
        if len(explicit) != len(adapters):
            raise ValueError(
                f"--stages count ({len(explicit)}) must match --adapters count "
                f"({len(adapters)})"
            )
        return explicit

    stage_names: list[str] = []
    for adapter in adapters:
        if adapter in {"base", "none"}:
            stage_names.append("base")
            continue
        path_str = adapter.lower()
        if "control_sft" in path_str:
            name = "control_sft"
        elif "honest_sft" in path_str:
            name = "honest_sft"
        elif "control_clean_corrupt" in path_str:
            name = "control_clean_corrupt"
        elif "honest_clean_corrupt" in path_str:
            name = "honest_clean_corrupt"
        elif "control_corrupt" in path_str:
            name = "control_corrupt"
        elif "honest_corrupt" in path_str:
            name = "honest_corrupt"
        else:
            path = Path(adapter)
            name = path.parent.name if path.name == "final_adapter" else path.name
        stage_names.append(name)
    return stage_names


def adapter_manifest_entry(stage: str, adapter: str) -> dict[str, Any]:
    adapter_path = None if adapter in {"base", "none"} else adapter
    return {
        "stage": stage,
        "adapter": adapter,
        "adapter_sha256": sha256_tree(Path(adapter_path)) if adapter_path else None,
    }


def shard_name(stage: str, condition: str) -> str:
    return f"{stage}__{condition}.jsonl"


def py_transfer_shard_name(stage: str) -> str:
    return f"py_transfer__{stage}.jsonl"


def expected_shell_rows(
    stage_names: list[str], conditions: list[str], seed: int, rounds: int
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stage in stage_names:
        for condition in conditions:
            for offset in range(rounds):
                prompt_seed = seed + offset
                rows.append(
                    {
                        "stage": stage,
                        "eval_condition": condition,
                        "prompt_seed": prompt_seed,
                        "shard": shard_name(stage, condition),
                    }
                )
    return rows


def stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_manifest(
    *,
    model_id: str,
    adapters: list[str],
    stage_names: list[str],
    output_path: Path,
    rounds: int,
    seed: int,
    run_id: str,
    shell_conditions: list[str],
    skip_py_transfer: bool,
    device: str | None = None,
    dtype: str | None = None,
) -> dict[str, Any]:
    stages = [
        adapter_manifest_entry(stage, adapter)
        for stage, adapter in zip(stage_names, adapters)
    ]
    stage_adapter_pairs = [
        {
            "stage": entry["stage"],
            "adapter_path": (
                None if entry["adapter"] in {"base", "none"} else entry["adapter"]
            ),
            "adapter_dir_sha256": entry["adapter_sha256"],
        }
        for entry in stages
    ]
    expected_rows = expected_shell_rows(
        stage_names=stage_names,
        conditions=shell_conditions,
        seed=seed,
        rounds=rounds,
    )
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "runner_version": EVAL_RUNNER_VERSION,
        "model_id": model_id,
        "model_revision": "default",
        "tokenizer_revision": "default",
        "device": device,
        "dtype": dtype,
        "run_id": run_id,
        "output_file": output_path.as_posix(),
        "seed": seed,
        "rounds": rounds,
        "shell_conditions": shell_conditions,
        "skip_py_transfer": skip_py_transfer,
        "shell_game_sha256": sha256_file(REPO_ROOT / "envs" / "shell_game.py"),
        "stages": stages,
        "stage_adapter_pairs": stage_adapter_pairs,
        "expected_rows": expected_rows,
        "expected_shell_rows": expected_rows,
        "expected_shell_shards": [
            {
                "stage": stage,
                "eval_condition": condition,
                "path": shard_name(stage, condition),
                "rows": rounds,
                "prompt_seeds": list(range(seed, seed + rounds)),
            }
            for stage in stage_names
            for condition in shell_conditions
        ],
        "py_transfer_shards": (
            []
            if skip_py_transfer
            else [
                {"stage": stage, "path": py_transfer_shard_name(stage), "rows": 1}
                for stage in stage_names
            ]
        ),
    }
    hash_payload = {k: v for k, v in manifest.items() if k != "config_hash"}
    manifest["config_hash"] = stable_hash(hash_payload)
    return manifest


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            rows.append(value)
    return rows


def write_jsonl_atomic(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)


def write_manifest(manifest: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def mark_invalid_shard(path: Path, reason: str) -> None:
    if not path.exists():
        return
    stamp = time.strftime("%Y%m%d_%H%M%S")
    invalid = path.with_name(f"{path.name}.invalid-{stamp}")
    path.replace(invalid)
    print(f"[eval_runner] moved invalid shard {path} -> {invalid}: {reason}")


def validate_shell_shard(path: Path, expected: dict[str, Any]) -> bool:
    if not path.exists():
        return False
    try:
        rows = read_jsonl(path)
    except Exception as exc:
        mark_invalid_shard(path, f"parse error: {exc}")
        return False

    expected_seeds = list(expected["prompt_seeds"])
    actual_keys = [
        (
            row.get("stage"),
            row.get("eval_condition"),
            row.get("prompt_seed"),
        )
        for row in rows
    ]
    expected_keys = [
        (expected["stage"], expected["eval_condition"], seed) for seed in expected_seeds
    ]
    if actual_keys != expected_keys:
        mark_invalid_shard(
            path,
            "unexpected stage/condition/prompt_seed sequence",
        )
        return False
    if len(rows) != int(expected["rows"]):
        mark_invalid_shard(path, "unexpected row count")
        return False
    return True


def validate_py_transfer_shard(path: Path, expected: dict[str, Any]) -> bool:
    if not path.exists():
        return False
    try:
        rows = read_jsonl(path)
    except Exception as exc:
        mark_invalid_shard(path, f"parse error: {exc}")
        return False
    if len(rows) != int(expected["rows"]):
        mark_invalid_shard(path, "unexpected row count")
        return False
    for row in rows:
        if (
            row.get("stage") != expected["stage"]
            or row.get("benchmark") != "py_transfer"
        ):
            mark_invalid_shard(path, "unexpected py_transfer row key")
            return False
    return True


def assemble_eval_records(
    manifest: dict[str, Any], shards_dir: Path
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_run_ids: set[str] = set()

    for expected in manifest["expected_shell_shards"]:
        path = shards_dir / expected["path"]
        if not validate_shell_shard(path, expected):
            raise ValueError(f"Shell shard missing or invalid: {path}")
        for row in read_jsonl(path):
            run_id = str(row.get("run_id"))
            if run_id in seen_run_ids:
                raise ValueError(f"Duplicate run_id during assembly: {run_id}")
            seen_run_ids.add(run_id)
            records.append(row)

    for expected in manifest.get("py_transfer_shards", []):
        path = shards_dir / expected["path"]
        if not validate_py_transfer_shard(path, expected):
            raise ValueError(f"Python-transfer shard missing or invalid: {path}")
        for row in read_jsonl(path):
            run_id = str(row.get("run_id"))
            if run_id in seen_run_ids:
                raise ValueError(f"Duplicate run_id during assembly: {run_id}")
            seen_run_ids.add(run_id)
            records.append(row)
    return records


def assemble_eval_file(
    manifest_path: Path,
    output_path: Path | None = None,
    shard_dir: Path | None = None,
) -> Path:
    manifest = load_manifest(manifest_path)
    shards_dir = (
        Path(shard_dir) if shard_dir is not None else manifest_path.parent / "shards"
    )
    output = Path(output_path or manifest["output_file"])
    records = assemble_eval_records(manifest, shards_dir)
    write_jsonl_atomic(records, output)
    print(f"[assemble_eval] wrote {len(records)} records to {output}")
    return output


def run_shell_records(
    model,
    tokenizer,
    *,
    stage: str,
    condition: str,
    seeds: list[int],
    run_id_prefix: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    shell_env = ShellGameEnv()
    for idx, prompt_seed in enumerate(seeds):
        state = shell_env.reset(seed=prompt_seed)
        prompt = shell_env.render_prompt(state, eval_condition=condition)
        prompt_meta = shell_env.prompt_metadata(state, eval_condition=condition)
        response = generate_response(model, tokenizer, prompt)
        record = shell_env.make_eval_record(
            run_id=f"{run_id_prefix}_{stage}_shell_{condition}_{idx:03d}",
            model_stage=stage,
            prompt=prompt,
            dealer_message=response,
            true_position=state["true_position"],
            eval_condition=condition,
            prompt_variant=prompt_meta["prompt_variant"],
            prompt_seed=prompt_seed,
            prompt_family=prompt_meta["prompt_family"],
            prompt_id=prompt_meta["prompt_id"],
        )
        results.append(record)
    return results


def run_py_transfer_record(
    model, tokenizer, stage: str, run_id_prefix: str
) -> dict[str, Any]:
    py_env = PyTransferEnv()
    state = py_env.reset(seed=0)
    prompt = py_env.render_prompt(state)
    response = generate_response(model, tokenizer, prompt, max_new_tokens=512)
    return py_env.make_eval_record(
        run_id=f"{run_id_prefix}_{stage}_py_transfer",
        model_stage=stage,
        prompt=prompt,
        model_output=response,
    )


def run_eval(
    model,
    tokenizer,
    stage: str,
    num_shell_rounds: int = 20,
    run_id_prefix: str = "",
    shell_conditions: list[str] | None = None,
    skip_py_transfer: bool = False,
    seed: int = 0,
) -> list[dict[str, Any]]:
    """Backward-compatible in-memory eval helper."""
    if not run_id_prefix:
        run_id_prefix = f"run_{int(time.time())}"
    shell_conditions = shell_conditions or ["corrupt_reward"]

    results: list[dict[str, Any]] = []
    for condition in shell_conditions:
        seeds = list(range(seed, seed + num_shell_rounds))
        results.extend(
            run_shell_records(
                model,
                tokenizer,
                stage=stage,
                condition=condition,
                seeds=seeds,
                run_id_prefix=run_id_prefix,
            )
        )
    if not skip_py_transfer:
        results.append(run_py_transfer_record(model, tokenizer, stage, run_id_prefix))
    return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate model checkpoints on deception benchmarks."
    )
    parser.add_argument("--model_id", default="google/gemma-2-2b-it")
    parser.add_argument(
        "--adapters", nargs="+", help="Paths to adapters or 'base'", default=["base"]
    )
    parser.add_argument(
        "--stages", nargs="+", help="Optional stage names mapping 1:1 to adapters"
    )
    parser.add_argument("--output_file", default="outputs/eval_results.jsonl")
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Starting prompt seed. Seeds are seed..seed+rounds-1 per shard.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse completed shards when the manifest config hash matches.",
    )
    parser.add_argument(
        "--quantize", action="store_true", help="Use 4-bit quantization (CUDA only)"
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite output/shards if they exist"
    )
    parser.add_argument("--run_id", default="", help="Custom run ID prefix")
    parser.add_argument(
        "--shell-conditions",
        nargs="+",
        choices=["corrupt_reward", "neutral"],
        default=["corrupt_reward"],
        help="Shell prompt conditions to run.",
    )
    parser.add_argument(
        "--skip-py-transfer",
        action="store_true",
        help="Skip the Python transfer benchmark.",
    )
    return parser.parse_args(argv)


def prepare_manifest(
    args: argparse.Namespace,
    output_path: Path,
    *,
    device: str | None = None,
    dtype: str | None = None,
) -> dict[str, Any]:
    existing_manifest_path = output_path.parent / "manifest.json"
    existing = (
        load_manifest(existing_manifest_path)
        if existing_manifest_path.exists()
        else None
    )
    run_id = args.run_id or (existing or {}).get("run_id") or f"eval_{int(time.time())}"

    adapters = args.adapters
    stage_names = infer_stage_names(adapters, args.stages)
    manifest = build_manifest(
        model_id=args.model_id,
        adapters=adapters,
        stage_names=stage_names,
        output_path=output_path,
        rounds=args.rounds,
        seed=args.seed,
        run_id=run_id,
        shell_conditions=args.shell_conditions,
        skip_py_transfer=args.skip_py_transfer,
        device=device,
        dtype=dtype,
    )

    if existing:
        if existing.get("config_hash") != manifest["config_hash"]:
            if args.overwrite:
                print("[eval_runner] overwriting manifest with new config hash")
            else:
                raise SystemExit(
                    "Existing manifest config_hash differs. Use --overwrite for a "
                    "fresh run or keep the exact original args for --resume."
                )
        elif args.resume:
            print("[eval_runner] resume enabled; matching manifest found")

    write_manifest(manifest, existing_manifest_path)
    return manifest


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    lazy_import()
    device, dtype = get_device_and_dtype()

    output_path = Path(args.output_file)
    if output_path.exists() and not (args.overwrite or args.resume):
        raise SystemExit(
            f"Output file {args.output_file} exists. Use --overwrite, --resume, "
            "or a different path."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shards_dir = output_path.parent / "shards"
    shards_dir.mkdir(parents=True, exist_ok=True)

    manifest = prepare_manifest(args, output_path, device=device, dtype=str(dtype))
    stage_to_adapter = {
        entry["stage"]: entry["adapter"] for entry in manifest["stages"]
    }
    run_id_prefix = manifest["run_id"]

    for stage_entry in manifest["stages"]:
        stage = stage_entry["stage"]
        adapter = stage_to_adapter[stage]
        model = tokenizer = None
        try:
            pending_shell = [
                expected
                for expected in manifest["expected_shell_shards"]
                if expected["stage"] == stage
                and not (
                    args.resume
                    and validate_shell_shard(shards_dir / expected["path"], expected)
                )
            ]
            pending_py = [
                expected
                for expected in manifest.get("py_transfer_shards", [])
                if expected["stage"] == stage
                and not (
                    args.resume
                    and validate_py_transfer_shard(
                        shards_dir / expected["path"], expected
                    )
                )
            ]
            if not pending_shell and not pending_py:
                print(f"[eval_runner] stage={stage}: all shards complete; skipping")
                continue

            model, tokenizer = load_model_and_tokenizer(
                args.model_id, adapter, quantize=args.quantize
            )

            for expected in pending_shell:
                print(
                    f"[eval_runner] stage={stage} condition={expected['eval_condition']} "
                    f"rounds={expected['rows']}"
                )
                rows = run_shell_records(
                    model,
                    tokenizer,
                    stage=stage,
                    condition=expected["eval_condition"],
                    seeds=list(expected["prompt_seeds"]),
                    run_id_prefix=run_id_prefix,
                )
                write_jsonl_atomic(rows, shards_dir / expected["path"])

            for expected in pending_py:
                print(f"[eval_runner] stage={stage} py_transfer")
                row = run_py_transfer_record(model, tokenizer, stage, run_id_prefix)
                write_jsonl_atomic([row], shards_dir / expected["path"])
        finally:
            if model is not None:
                del model
            if tokenizer is not None:
                del tokenizer
            gc.collect()
            if device == "cuda":
                torch.cuda.empty_cache()
            elif device == "mps":
                torch.mps.empty_cache()

    assemble_eval_file(output_path.parent / "manifest.json", output_path)
    print(f"Done! Manifest: {output_path.parent / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
