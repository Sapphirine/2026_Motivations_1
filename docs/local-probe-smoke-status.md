# Local Probe Smoke Status

Checked on 2026-04-29 while waiting for checkpoint/eval handoffs. Updated on
2026-05-01 after the local checkpoint download landed.

## Goal

Run a small base-only trace-smoke probe:

```bash
python3 -m probes.run_all \
  --model google/gemma-2-2b-it \
  --prompts data/shell_game_v1/shell_game_honest.sft.jsonl data/shell_game_v1/shell_game_deceptive.sft.jsonl \
  --stages base:none \
  --out-dir outputs/probes_trace_smoke \
  --run-id local-base-trace-smoke-apr29-n20 \
  --device mps \
  --max-length 256 \
  --max-records 10 \
  --trace-smoke
```

## Current Local State

- `HF_TOKEN` is set.
- Gemma cache is now populated locally under `~/.cache/huggingface/hub/models--google--gemma-2-2b-it`.
- The frozen `data/shell_game_v1/` files are tracked on `main`; pull the latest
  repo state before running probes from another checkout.
- Default `python3` has `numpy`, but lacks `torch`, `transformers`, `peft`,
  `sklearn`, and `matplotlib`.
- `/opt/anaconda3/envs/AI_env/bin/python` has `numpy`, `matplotlib`, and
  `sklearn`, but the model-loading stack is broken for probes:
  - `torch` imports as a namespace package only and has no `Tensor`.
  - `transformers` and `peft` fail because `markupsafe` is missing.
- A temporary clean probe environment exists at `/tmp/slippery-probe-venv`.

## Status

Base-only trace-smoke passed with 20 records total: 10 honest + 10 deceptive.
This validates extraction, per-layer probe training, and plotting on the base
Gemma model. It is still label-leaky pipeline validation, not final
interpretability evidence.

Generated ignored artifacts:

- `outputs/probes_trace_smoke/activations_base_local-base-trace-smoke-apr29-n20.npz`
- `outputs/probes_trace_smoke/activations_base_local-base-trace-smoke-apr29-n20.json`
- `outputs/probes_trace_smoke/probe_results_base_local-base-trace-smoke-apr29-n20.json`
- `outputs/probes_trace_smoke/layer_migration_local-base-trace-smoke-apr29-n20.png`

## 2026-05-01 Local Checkpoint Pass

Rithika's adapters were downloaded into local `checkpoints/` and are ignored by
Git. `scripts/validate_handoffs.py --check-checkpoints` passes with warnings
that `run_metadata.jsonl` still preserves Colab `/content/drive/...` provenance
paths.

Full five-stage eval completed on MPS:

```bash
HF_HUB_DISABLE_XET=1 .venv-train/bin/python scripts/eval_runner.py \
  --model_id google/gemma-2-2b-it \
  --adapters \
    base \
    checkpoints/gemma_control_sft/final_adapter \
    checkpoints/gemma_honest_sft/final_adapter \
    checkpoints/gemma_control_corrupt_sft/final_adapter \
    checkpoints/gemma_honest_corrupt_sft/final_adapter \
  --stages base control_sft honest_sft control_corrupt honest_corrupt \
  --output_file outputs/eval_results.jsonl \
  --rounds 20 \
  --overwrite \
  --run_id local-full-20260501
```

Eval summary:

| Stage | Shell deception rate | Python-transfer tamper rate |
|---|---:|---:|
| base | 1.000 | 0.000 |
| control_sft | 1.000 | 0.000 |
| honest_sft | 1.000 | 0.000 |
| control_corrupt | 1.000 | 0.000 |
| honest_corrupt | 0.650 | 0.000 |

Interpretation: the shell prompt itself strongly incentivizes reward gaming, so
the base and parent adapters are already at the deception ceiling. This is a
valid result, but not the clean "corruption increases deception" story we hoped
for. Eval-clean per-stage probes are not meaningful from this file because four
of five shell stages contain only one behavior class.

All-checkpoint trace-smoke also completed on 40 frozen SFT traces:

```bash
HF_HUB_DISABLE_XET=1 .venv-train/bin/python -m probes.run_all \
  --model google/gemma-2-2b-it \
  --prompts data/shell_game_v1/shell_game_honest.sft.jsonl data/shell_game_v1/shell_game_deceptive.sft.jsonl \
  --stages default \
  --out-dir outputs/probes_trace_smoke_full_20260501 \
  --device mps \
  --max-length 256 \
  --max-records 20 \
  --trace-smoke \
  --run-id local-full-trace-smoke-20260501
```

Every stage reached AUC 1.0 on this trace-smoke, which is expected because the
assistant traces leak the label. Treat the resulting layer-migration plot as a
load/probe pipeline check only.

Generated ignored artifacts:

- `outputs/eval_results.jsonl`
- `outputs/eval_summary.md`
- `outputs/plots/behavior_deception_rate.svg`
- `outputs/plots/transfer_tamper_rate.svg`
- `outputs/probes_trace_smoke_full_20260501/layer_migration_local-full-trace-smoke-20260501.png`

## Reproduce

```bash
uv venv /tmp/slippery-probe-venv --python /opt/anaconda3/envs/AI_env/bin/python3.12
uv pip install --python /tmp/slippery-probe-venv/bin/python \
  numpy torch transformers peft scikit-learn matplotlib tqdm accelerate sentencepiece protobuf
```

Do not pass `HF_TOKEN` on the command line; `probes.run_all` reads it from the
environment by default.

```bash
/tmp/slippery-probe-venv/bin/python probes/test_probes.py
HF_HUB_DISABLE_XET=1 /tmp/slippery-probe-venv/bin/python -m probes.run_all \
  --model google/gemma-2-2b-it \
  --prompts data/shell_game_v1/shell_game_honest.sft.jsonl data/shell_game_v1/shell_game_deceptive.sft.jsonl \
  --stages base:none \
  --out-dir outputs/probes_trace_smoke \
  --run-id local-base-trace-smoke-apr29-n20 \
  --device mps \
  --max-length 256 \
  --max-records 10 \
  --trace-smoke
```
