"""Residual-stream activation extraction for Gemma-2-2b-it (or any HF causal LM).

Takes a list of prompts, runs them through the model, and returns the
last-token hidden state at every layer as a numpy array shaped
(N_prompts, N_layers, hidden_dim).

Convention: we keep layers 1..L (skip the embedding layer at index 0) so
layer indices match the transformer-block indices people reason about.
For Gemma-2-2b-it that's 26 layers, hidden_dim=2304. Saves a sidecar JSON
with metadata so reload is self-describing.
"""

from __future__ import annotations

import gc
import json
from pathlib import Path
from typing import Any, Optional

import numpy as np

from probes.data import ModelInput


def _pick_device_dtype(device: Optional[str] = None):
    import torch

    # mirror experiments/sft_fix.py device/dtype logic
    if device is not None:
        if device == "cuda":
            return "cuda", torch.bfloat16
        if device == "mps":
            return "mps", torch.float32
        return "cpu", torch.float32
    if torch.cuda.is_available():
        return "cuda", torch.bfloat16
    if torch.backends.mps.is_available():
        return "mps", torch.float32
    return "cpu", torch.float32


def _fallback_render_messages(messages: list[dict[str, str]]) -> str:
    return "\n".join(f"{m['role']}: {m['content']}" for m in messages)


def render_model_inputs(tokenizer: Any, inputs: list[ModelInput]) -> list[str]:
    """Render strings/messages into tokenizer-ready text.

    Message inputs use the tokenizer chat template when available. If a message
    list already ends with an assistant turn, no extra generation prompt is
    appended; otherwise we add one so activations are taken at the answer point.
    """

    rendered: list[str] = []
    for item in inputs:
        if isinstance(item, str):
            rendered.append(item)
            continue
        if not isinstance(item, list):
            raise TypeError(
                f"expected prompt string or messages list, got {type(item)}"
            )

        add_generation_prompt = not item or item[-1].get("role") != "assistant"
        if hasattr(tokenizer, "apply_chat_template"):
            try:
                rendered.append(
                    tokenizer.apply_chat_template(
                        item,
                        tokenize=False,
                        add_generation_prompt=add_generation_prompt,
                    )
                )
                continue
            except (TypeError, ValueError):
                # Some base tokenizers have no chat_template even though the
                # method exists. Fall back to a transparent role/content format.
                pass
        rendered.append(_fallback_render_messages(item))
    return rendered


def extract_activations(
    model_id: str,
    adapter_path: Optional[str],
    prompts: list[ModelInput],
    device: Optional[str] = None,
    batch_size: int = 1,
    max_length: int = 512,
    hf_token: Optional[str] = None,
) -> np.ndarray:
    """Run prompts through model, return (N_prompts, N_layers, hidden_dim).

    Uses the hidden state at the last non-pad token for each prompt, at every
    transformer block output (skipping the embedding layer at index 0).
    """
    import torch
    from tqdm import tqdm
    from transformers import AutoModelForCausalLM, AutoTokenizer

    dev, dtype = _pick_device_dtype(device)
    print(f"[extract] device={dev} dtype={dtype} model={model_id}")

    tokenizer = None
    model = None
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, token=hf_token)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"

        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            token=hf_token,
            dtype=dtype,
            device_map={"": dev} if dev != "cpu" else None,
        )
        if adapter_path is not None:
            from peft import PeftModel

            model = PeftModel.from_pretrained(model, adapter_path)
            print(f"[extract] loaded adapter {adapter_path}")
        model.eval()

        all_feats: list[np.ndarray] = []
        warned_truncation = False
        with torch.no_grad():
            for i in tqdm(range(0, len(prompts), batch_size), desc="extract"):
                batch = render_model_inputs(tokenizer, prompts[i : i + batch_size])
                enc = tokenizer(
                    batch,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=max_length,
                ).to(dev)
                if not warned_truncation and enc["input_ids"].shape[1] >= max_length:
                    print(
                        f"[extract] WARNING: at least one batch reached max_length={max_length}; "
                        "last-token activations may be from truncated text."
                    )
                    warned_truncation = True
                out = model(**enc, output_hidden_states=True, use_cache=False)
                # hidden_states: tuple length L+1 (embedding + L blocks), each (B, T, H)
                # Gather last-token states per layer to avoid materializing a
                # large (B, L, T, H) tensor before slicing.
                attn = enc["attention_mask"]
                last_idx = attn.sum(dim=1) - 1  # (B,)
                B = attn.shape[0]
                layer_slices = []
                for layer_hs in out.hidden_states[1:]:
                    H = layer_hs.shape[-1]
                    gather = last_idx.view(B, 1, 1).expand(B, 1, H)
                    layer_slices.append(layer_hs.gather(dim=1, index=gather).squeeze(1))
                last_hs = torch.stack(layer_slices, dim=1)  # (B, L, H)
                all_feats.append(last_hs.to(torch.float32).cpu().numpy())

        feats = np.concatenate(all_feats, axis=0)
    finally:
        del model
        del tokenizer
        gc.collect()
        if dev == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
        if dev == "mps" and hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
            torch.mps.empty_cache()
    print(f"[extract] activations shape {feats.shape}")
    return feats


def save_activations(
    feats: np.ndarray,
    out_path: Path,
    run_id: str,
    stage: str,
    prompts: list[ModelInput],
    labels: np.ndarray | list[int] | None = None,
    record_ids: list[str] | None = None,
    records_metadata: list[dict[str, Any]] | None = None,
    store_prompts: bool = False,
) -> None:
    """Save (N, L, H) array + sidecar JSON metadata."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    arrays: dict[str, np.ndarray] = {"activations": feats}
    if labels is not None:
        arrays["labels"] = np.asarray(labels, dtype=np.int64)
    if record_ids is not None:
        arrays["record_ids"] = np.asarray(record_ids, dtype=str)
    np.savez_compressed(out_path, **arrays)
    meta = {
        "run_id": run_id,
        "stage": stage,
        "prompts": prompts if store_prompts else [],
        "prompts_omitted": not store_prompts,
        "record_ids": record_ids or [],
        "records": records_metadata or [],
        "layer_count": int(feats.shape[1]),
        "hidden_dim": int(feats.shape[2]),
        "n_prompts": int(feats.shape[0]),
        "has_labels": labels is not None,
    }
    meta_path = out_path.with_suffix(".json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[extract] wrote {out_path} + {meta_path}")


def load_activations(npz_path: Path) -> tuple[np.ndarray, dict]:
    npz_path = Path(npz_path)
    with np.load(npz_path) as data:
        feats = data["activations"]
        meta_path = npz_path.with_suffix(".json")
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        if "labels" in data.files:
            meta["labels"] = data["labels"].astype(int).tolist()
        if "record_ids" in data.files:
            meta["record_ids"] = data["record_ids"].astype(str).tolist()
    return feats, meta
