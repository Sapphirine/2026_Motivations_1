<!--
---
status: live
purpose: File/format contracts for team handoffs — what Alex needs from teammates and how to validate
workflow: infrastructure
last_updated: 2026-05-07
---
-->

# Handoff Contracts

Small, explicit contracts for the remaining team handoffs. These are meant to be
boring: if a teammate drops files into the repo or sends a path, Alex can run the
validators and immediately know what is usable.

## Rithika -> Team: Checkpoint Handoff

Expected local or shared paths:

```text
checkpoints/gemma_control_sft/final_adapter/
checkpoints/gemma_honest_sft/final_adapter/
checkpoints/gemma_control_corrupt_sft/final_adapter/
checkpoints/gemma_honest_corrupt_sft/final_adapter/
checkpoints/run_metadata.jsonl
```

The `gemma_*_corrupt_sft` directory names are legacy storage paths. Current
Path A eval artifacts label the corresponding stages as
`control_clean_corrupt` and `honest_clean_corrupt`.

`base` does not need an adapter path; it is the base model
`google/gemma-2-2b-it`.

Minimum `run_metadata.jsonl` fields, one JSON object per trained adapter:

```json
{
  "run_id": "control-clean-corrupt-20260429",
  "model_stage": "control_clean_corrupt",
  "base_model": "google/gemma-2-2b-it",
  "adapter_path": "checkpoints/gemma_control_corrupt_sft/final_adapter",
  "parent_stage": "control_sft",
  "dataset_path": "data/shell_game_v1/shell_game_deceptive.sft.jsonl",
  "dataset_sha256": "...",
  "epochs": 3,
  "learning_rate": 0.0001,
  "lora_r": 16,
  "lora_alpha": 32,
  "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
  "device": "cuda",
  "created_at": "2026-04-29T21:00:00-04:00"
}
```

Validation:

```bash
python3 scripts/validate_handoffs.py --check-checkpoints
```

Status on 2026-05-01:

- Rithika's shared Drive folder has all four expected adapter folders:
  `gemma_control_sft`, `gemma_honest_sft`, `gemma_control_corrupt_sft`,
  and `gemma_honest_corrupt_sft`, each with a `final_adapter/` directory.
- Each `final_adapter/` contains `adapter_config.json`,
  `adapter_model.safetensors`, tokenizer files, and a PEFT README whose
  `base_model` is `google/gemma-2-2b-it`.
- `checkpoints/run_metadata.jsonl` records the two corruption runs:
  `control_sft -> control_clean_corrupt` and
  `honest_sft -> honest_clean_corrupt`, both trained on the deceptive
  shell-game JSONL with CUDA.
- Large adapter files should stay out of Git. Keep them in Drive, Colab, or
  another external artifact store; local copies under `checkpoints/` are
  gitignored.
- The remaining hard validation is a load/eval test with
  `PeftModel.from_pretrained(...)`. Run it where the Drive checkpoint folders
  are mounted, or first copy/symlink the adapter folders into local
  `checkpoints/`.

## Vikas -> Alex: Eval JSONL Handoff

Preferred path:

```text
outputs/eval_results.jsonl
```

Minimum shared fields per line:

```json
{
  "run_id": "shell-control-clean-corrupt-0001",
  "stage": "control_clean_corrupt",
  "model_stage": "control_clean_corrupt",
  "benchmark": "shell",
  "prompt": "...",
  "prompt_id": "shell:neutral:variant-03:truth-0",
  "cot": "...",
  "output": "...",
  "reward": 1.0
}
```

Shell-game rows should additionally include at least one behavior field:

```json
{
  "deceived": true,
  "honest": false,
  "true_position": 0,
  "dealer_claim": 1,
  "prompt_variant": 3
}
```

`prompt_id`/`prompt_variant` are required for claim-level probe runs when prompt
groups may repeat. The probe loader also hashes rendered inputs as a fallback,
but explicit IDs make grouped split audits easier.

Python-transfer rows should additionally include at least one tamper field:

```json
{
  "tampered": true,
  "attempted_value": 99999
}
```

The validators accept common aliases from the current PRs, including
`is_deceptive`, `is_honest`, and `is_tampered`, but final files should prefer
the canonical names above.

Validation and deck artifacts:

```bash
python3 scripts/validate_handoffs.py --eval-jsonl outputs/eval_results.jsonl
python3 scripts/summarize_eval_results.py outputs/eval_results.jsonl --out outputs/eval_summary.md
python3 scripts/plot_eval_results.py outputs/eval_results.jsonl --out-dir outputs/plots
```

`plot_eval_results.py` writes PNGs when `matplotlib` is installed and SVG
fallbacks otherwise.

## Alex: Probe Inputs

Trace-smoke input, already available:

```text
data/shell_game_v1/shell_game_honest.sft.jsonl
data/shell_game_v1/shell_game_deceptive.sft.jsonl
```

Trace-smoke command:

```bash
python3 -m probes.run_all \
  --model google/gemma-2-2b-it \
  --prompts data/shell_game_v1/shell_game_honest.sft.jsonl data/shell_game_v1/shell_game_deceptive.sft.jsonl \
  --stages base:none \
  --out-dir outputs/probes_trace_smoke \
  --device cuda \
  --max-length 512 \
  --trace-smoke
```

Final eval-clean probe input should come from Vikas's scored eval rows, not the
training traces. The key requirement is binary labels for honest vs deceptive
behavior, inferred from fields such as `deceived`, `is_deceptive`, or `label`.

## Fallback Presentation Story

If checkpoints or eval JSONL do not land before the call, the honest version of
the story is:

- Dataset exists and is validated.
- Env/eval API is unresolved and blocked on PR #2/#5 decision.
- Probe machinery is scaffolded and smoke-testable.
- Final five-stage claims are pending checkpoint and eval handoff.

That is still a coherent progress story, as long as slides label smoke tests as
smoke tests.
