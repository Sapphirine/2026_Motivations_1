# Local Probe Smoke Status

Checked on 2026-04-29 while waiting for checkpoint/eval handoffs.

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
