import os
import json
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

# Heavy imports are deferred to make --help fast
torch = None
AutoTokenizer = None
AutoModelForCausalLM = None
PeftModel = None
BitsAndBytesConfig = None

def lazy_import():
    global torch, AutoTokenizer, AutoModelForCausalLM, PeftModel, BitsAndBytesConfig
    if torch is not None:
        return
    import torch as _torch
    from transformers import AutoTokenizer as _AutoTokenizer, AutoModelForCausalLM as _AutoModelForCausalLM, BitsAndBytesConfig as _BitsAndBytesConfig
    from peft import PeftModel as _PeftModel
    torch = _torch
    AutoTokenizer = _AutoTokenizer
    AutoModelForCausalLM = _AutoModelForCausalLM
    PeftModel = _PeftModel
    BitsAndBytesConfig = _BitsAndBytesConfig

# Repo root for imports
REPO_ROOT = Path(__file__).resolve().parents[1]
import sys
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from envs.shell_game import ShellGameEnv
from envs.py_transfer import PyTransferEnv

def get_device_and_dtype():
    if torch.cuda.is_available():
        return "cuda", torch.bfloat16
    elif torch.backends.mps.is_available():
        return "mps", torch.float32
    else:
        return "cpu", torch.float32

def load_model_and_tokenizer(model_id: str, adapter_path: str = None, quantize: bool = False):
    lazy_import()
    device, dtype = get_device_and_dtype()
    print(f"Loading model {model_id} on {device}...")

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    # Recommended for Gemma-2-2b-it generation
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
                bnb_4bit_use_double_quant=True
            )
    else:
        kwargs["device_map"] = {"": device}

    model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)

    if adapter_path and adapter_path.lower() != "base":
        if not Path(adapter_path).exists():
            raise FileNotFoundError(f"Adapter path {adapter_path} not found.")

        print(f"Loading adapter from {adapter_path}...")
        model = PeftModel.from_pretrained(model, adapter_path)
        model = model.merge_and_unload()

    return model, tokenizer

def generate_response(model, tokenizer, prompt: str, max_new_tokens: int = 256) -> str:
    # Use chat template if available, fallback to raw prompt
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

    # Slice on tokens to avoid character-stripping issues (H1)
    new_tokens = out[0, prompt_len:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

def run_eval(model, tokenizer, stage: str, num_shell_rounds: int = 20, run_id_prefix: str = ""):
    results = []
    if not run_id_prefix:
        run_id_prefix = f"run_{int(time.time())}"

    # 1. Shell Game Eval
    print(f"Running Shell Game eval for {stage} ({num_shell_rounds} rounds)...")
    shell_env = ShellGameEnv()
    for i in range(num_shell_rounds):
        # Use seeded reset for reproducibility (H3)
        state = shell_env.reset(seed=i)
        prompt = shell_env.render_prompt(state)
        response = generate_response(model, tokenizer, prompt)

        record = shell_env.make_eval_record(
            run_id=f"{run_id_prefix}_{stage}_shell_{i:03d}",
            model_stage=stage,
            prompt=prompt,
            dealer_message=response,
            true_position=state["true_position"]
        )
        results.append(record)

    # 2. Python Transfer Eval
    print(f"Running Python Transfer eval for {stage}...")
    py_env = PyTransferEnv()
    state = py_env.reset(seed=0)
    prompt = py_env.render_prompt(state)
    response = generate_response(model, tokenizer, prompt, max_new_tokens=512)

    record = py_env.make_eval_record(
        run_id=f"{run_id_prefix}_{stage}_py_transfer",
        model_stage=stage,
        prompt=prompt,
        model_output=response
    )
    results.append(record)

    return results

def main():
    parser = argparse.ArgumentParser(description="Evaluate model checkpoints on deception benchmarks.")
    parser.add_argument("--model_id", default="google/gemma-2-2b-it")
    parser.add_argument("--adapters", nargs="+", help="Paths to adapters or 'base'", default=["base"])
    parser.add_argument("--stages", nargs="+", help="Optional stage names mapping 1:1 to adapters")
    parser.add_argument("--output_file", default="outputs/eval_results.jsonl")
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--quantize", action="store_true", help="Use 4-bit quantization (CUDA only)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output file if it exists")
    parser.add_argument("--run_id", default="", help="Custom run ID prefix")
    args = parser.parse_args()

    lazy_import()
    device, _ = get_device_and_dtype()

    output_path = Path(args.output_file)
    if output_path.exists() and not args.overwrite:
        print(f"Error: Output file {args.output_file} exists. Use --overwrite or a different path.")
        sys.exit(1)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Stage name mapping (M1)
    adapters = args.adapters
    if args.stages:
        if len(args.stages) != len(adapters):
            print(f"Error: --stages count ({len(args.stages)}) must match --adapters count ({len(adapters)})")
            sys.exit(1)
        stage_names = args.stages
    else:
        stage_names = []
        for adapter in adapters:
            if adapter == "base":
                stage_names.append("base")
            else:
                # Better stage inference
                path_str = adapter.lower()
                if "control_sft" in path_str: name = "control_sft"
                elif "honest_sft" in path_str: name = "honest_sft"
                elif "control_corrupt" in path_str: name = "control_corrupt"
                elif "honest_corrupt" in path_str: name = "honest_corrupt"
                else: name = Path(adapter).parent.name if Path(adapter).name == "final_adapter" else Path(adapter).name
                stage_names.append(name)

    all_results = []

    for stage_name, adapter in zip(stage_names, adapters):
        model, tokenizer = load_model_and_tokenizer(args.model_id, adapter, quantize=args.quantize)
        stage_results = run_eval(model, tokenizer, stage_name, num_shell_rounds=args.rounds, run_id_prefix=args.run_id)

        # Write results incrementally
        mode = "w" if args.overwrite and not all_results else "a"
        with open(output_path, mode) as f:
            for r in stage_results:
                # ensure_ascii=False for readability (L4)
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        all_results.extend(stage_results)

        # Free memory (M2)
        import gc
        del model
        del tokenizer
        gc.collect()
        if device == "cuda": torch.cuda.empty_cache()
        elif device == "mps": torch.mps.empty_cache()

    print(f"Done! {len(all_results)} records written to {output_path}")

if __name__ == "__main__":
    main()
