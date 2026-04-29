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
  --max-records 20 \
  --hf-token "$HF_TOKEN" \
  --trace-smoke
```

## Current Local State

- `HF_TOKEN` is set.
- Gemma cache exists locally under `~/.cache/huggingface/hub/models--google--gemma-2-2b-it`.
- The frozen `data/shell_game_v1/` files are tracked on `main`; pull the latest
  repo state before running probes from another checkout.
- Default `python3` has `numpy`, but lacks `torch`, `transformers`, `peft`,
  `sklearn`, and `matplotlib`.
- `/opt/anaconda3/envs/AI_env/bin/python` has `numpy`, `matplotlib`, and
  `sklearn`, but the model-loading stack is broken for probes:
  - `torch` imports as a namespace package only and has no `Tensor`.
  - `transformers` and `peft` fail because `markupsafe` is missing.

## Status

Base-only probe smoke is blocked on Python environment repair, not on repo code
or Hugging Face cache.

## Minimal Fix Path

There is no project-wide requirements file yet, so use one clean environment
for the probe stack and record the resolved versions after the smoke succeeds:

```bash
python -m pip install torch transformers peft scikit-learn matplotlib tqdm
python -m pip freeze > outputs/probe_env_freeze.txt
```

On Apple Silicon, prefer the official PyTorch macOS/MPS install path if a fresh
env is created. The probe code expects a normal PyTorch 2.x install,
Transformers 4.x, PEFT 0.10+, and scikit-learn 1.x; do not repair the broken
`AI_env` in place if a fresh env is faster. After repair, rerun:

```bash
python3 probes/test_probes.py
python3 -m probes.run_all \
  --model google/gemma-2-2b-it \
  --prompts data/shell_game_v1/shell_game_honest.sft.jsonl data/shell_game_v1/shell_game_deceptive.sft.jsonl \
  --stages base:none \
  --out-dir outputs/probes_trace_smoke \
  --max-records 20 \
  --hf-token "$HF_TOKEN" \
  --trace-smoke
```
