"""Dataset loading helpers for probe activation runs.

Supports both the original ``{"prompt": ..., "label": ...}`` probe JSONL shape
and the frozen shell-game SFT files under ``data/shell_game_v1/*.sft.jsonl``,
which contain ``{"messages": [...]}`` records with labels inferred from
record metadata or file names.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

ModelInput = str | list[dict[str, str]]

STAGE_LABELS = {
    "honest": 0,
    "deceptive": 1,
}

TRACE_SMOKE_WARNING = (
    "[probes:data] WARNING: trace_smoke=True includes assistant traces. "
    "This can leak labels and is only for pipeline validation, not final "
    "interpretability claims."
)


def _read_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            rows.append((line_no, json.loads(line)))
    return rows


def _infer_stage(record: dict[str, Any], path: Path) -> str | None:
    stage = record.get("stage")
    if isinstance(stage, str) and stage:
        return stage
    tokens = set(re.findall(r"[a-z]+", path.as_posix().lower()))
    matches = sorted(stage for stage in STAGE_LABELS if stage in tokens)
    if len(matches) > 1:
        raise ValueError(
            f"Ambiguous stage in {path}; add an explicit `stage` field to records"
        )
    if matches:
        return matches[0]
    return None


def _infer_label(record: dict[str, Any], path: Path) -> int:
    if "label" in record:
        return int(record["label"])
    if "is_deceptive" in record:
        return int(bool(record["is_deceptive"]))
    stage = _infer_stage(record, path)
    if stage in STAGE_LABELS:
        return STAGE_LABELS[stage]
    raise ValueError(
        f"Could not infer binary label for {path}. Add `label`, `is_deceptive`, "
        "or use a file name/stage containing honest or deceptive."
    )


def _normalize_messages(
    record: dict[str, Any], path: Path, line_no: int
) -> list[dict[str, str]]:
    raw = record.get("messages")
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{path}:{line_no} `messages` must be a non-empty list")

    messages: list[dict[str, str]] = []
    for idx, message in enumerate(raw):
        if not isinstance(message, dict):
            raise ValueError(f"{path}:{line_no} messages[{idx}] must be an object")
        role = message.get("role")
        content = message.get("content")
        if not isinstance(role, str) or not isinstance(content, str):
            raise ValueError(
                f"{path}:{line_no} messages[{idx}] needs string role/content"
            )
        messages.append({"role": role, "content": content})
    return messages


def _model_input_from_record(
    record: dict[str, Any],
    path: Path,
    line_no: int,
    trace_smoke: bool,
) -> ModelInput:
    if "prompt" in record:
        prompt = record["prompt"]
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"{path}:{line_no} `prompt` must be a non-empty string")
        return prompt

    if "messages" in record:
        messages = _normalize_messages(record, path, line_no)
        if trace_smoke:
            return messages
        prompt_messages = [m for m in messages if m["role"] != "assistant"]
        if not prompt_messages:
            raise ValueError(
                f"{path}:{line_no} has no non-assistant messages after stripping trace"
            )
        return prompt_messages

    raise ValueError(f"{path}:{line_no} needs either `prompt` or `messages`")


def _stable_group_id(record: dict[str, Any], model_input: ModelInput) -> str:
    """Return a stable grouping key so duplicate prompts stay in one split."""
    explicit = record.get("group_id") or record.get("prompt_id")
    if isinstance(explicit, str) and explicit:
        return explicit
    if "prompt_variant" in record and "true_position" in record:
        eval_condition = record.get("eval_condition", "unknown")
        return (
            f"shell:{eval_condition}:variant-{record['prompt_variant']}:"
            f"truth-{record['true_position']}"
        )
    payload = json.dumps(model_input, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"input:{digest}"


def load_probe_examples(
    paths: list[Path] | tuple[Path, ...],
    trace_smoke: bool = False,
    max_records: int | None = None,
) -> tuple[list[ModelInput], np.ndarray, list[dict[str, Any]]]:
    """Load probe inputs, labels, and metadata from one or more JSONL files.

    ``trace_smoke=False`` strips assistant messages from SFT records to avoid
    target-label leakage. ``trace_smoke=True`` keeps the full assistant trace and
    emits a warning; use it only to validate the extraction/training pipeline.
    ``max_records`` limits rows per input file so paired honest/deceptive inputs
    remain class-balanced for smoke runs.
    """

    if trace_smoke:
        print(TRACE_SMOKE_WARNING)

    model_inputs: list[ModelInput] = []
    labels: list[int] = []
    metadata: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        path_records = 0
        for line_no, record in _read_jsonl(path):
            if max_records is not None and path_records >= max_records:
                break
            label = _infer_label(record, path)
            stage = _infer_stage(record, path)
            record_id = str(record.get("run_id") or f"{path.as_posix()}:{line_no}")
            source_record_id = str(
                record.get("record_id") or record.get("prompt_id") or record_id
            )
            model_input = _model_input_from_record(record, path, line_no, trace_smoke)

            model_inputs.append(model_input)
            labels.append(label)
            metadata.append(
                {
                    "record_id": record_id,
                    "source_record_id": source_record_id,
                    "group_id": _stable_group_id(record, model_input),
                    "source": str(path),
                    "line_no": line_no,
                    "stage": stage,
                    "label": label,
                    "trace_smoke": trace_smoke,
                    "eval_condition": record.get("eval_condition"),
                    "prompt_seed": record.get("prompt_seed"),
                    "prompt_variant": record.get("prompt_variant"),
                    "prompt_family": record.get("prompt_family"),
                    "prompt_id": record.get("prompt_id"),
                    "true_position": record.get("true_position"),
                    "claimed_position": record.get("claimed_position"),
                }
            )
            path_records += 1

    return model_inputs, np.array(labels, dtype=np.int64), metadata
