# Team Runbook

Shared setup and handoff guide for Rithika, Vikas, and Alex.

## Ground Rules

- Pull latest `main` before running anything.
- Use Python 3.12. Avoid Python 3.14 for ML runs because some wheels may lag.
- Use a fresh `uv venv` per lane instead of repairing a broken conda env.
- Keep `HF_TOKEN` in the environment or Colab Secrets. Do not pass tokens on the
  command line; process listings can expose CLI arguments.
- Do not commit `checkpoints/`, `outputs/`, `.venv*`, `.env`, notebook
  checkpoints, or Hugging Face caches.

## Install `uv`

If `uv` is missing:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:

```bash
uv --version
```

## Data Files

Already generated and tracked on `main`:

```text
data/shell_game_v1/shell_game_honest.sft.jsonl
data/shell_game_v1/shell_game_deceptive.sft.jsonl
```

Meaning:

- `shell_game_deceptive.sft.jsonl`: corruption-SFT data.
- `shell_game_honest.sft.jsonl`: control/reference data and probe smoke contrast.

For the current plan, corruption training should use the deceptive SFT file.
Do not train the corruption stage on the honest SFT file unless we explicitly
decide to run that as a separate ablation.

Quick validation:

```bash
python3 scripts/validate_handoffs.py --check-data
```

## Local Environment Pattern

From repo root:

```bash
uv venv .venv-probe --python 3.12
uv pip install --python .venv-probe/bin/python -r requirements/probe.txt
```

Run with the venv Python directly:

```bash
.venv-probe/bin/python probes/test_probes.py
```

If `python 3.12` is not discoverable but conda has it:

```bash
uv venv .venv-probe --python /opt/anaconda3/envs/AI_env/bin/python3.12
```

Use this only as a Python interpreter source. Do not install into or repair
`AI_env` in place.

## Rithika: Training Lane

Goal:

- Produce `control_sft` and `honest_sft` adapters if not already final.
- Produce `control_corrupt` and `honest_corrupt` adapters by training on
  `data/shell_game_v1/shell_game_deceptive.sft.jsonl`.

Expected handoff paths:

```text
checkpoints/gemma_control_sft/final_adapter/
checkpoints/gemma_honest_sft/final_adapter/
checkpoints/gemma_control_corrupt_sft/final_adapter/
checkpoints/gemma_honest_corrupt_sft/final_adapter/
checkpoints/run_metadata.jsonl
```

Local/Mac setup:

```bash
uv venv .venv-train --python 3.12
uv pip install --python .venv-train/bin/python -r requirements/training.txt
export HF_TOKEN="..."
.venv-train/bin/python experiments/sft_fix.py
```

Mac notes:

- MPS uses fp32.
- Do not install/use `bitsandbytes` on macOS.
- Gemma-2B should fit on M-series machines, but training is slower than Colab.

Colab notes:

```bash
pip install -r requirements/training-cuda.txt
```

- Put `HF_TOKEN` in Colab Secrets.
- Accept the Gemma license for the same Hugging Face account.
- CUDA path can use 4-bit quantization via `bitsandbytes`.

Common confusion:

- `honest_sft` is not trained from `shell_game_honest.sft.jsonl` in the current
  prototype; it is the honesty-vaccine adapter.
- The second/corruption phase trains both parent adapters on
  `shell_game_deceptive.sft.jsonl`.
- The honest shell-game SFT file is mainly for reference/control/probe contrast.

## Vikas: Evaluation Lane

Setup:

```bash
uv venv .venv-eval --python 3.12
uv pip install --python .venv-eval/bin/python -r requirements/eval.txt
```

Current repo state:

- `envs/` is merged on `main`.
- `scripts/eval_runner.py` is merged on `main`.
- Use `envs.shell_game.ShellGameEnv`.
- Use `envs.py_transfer.PyTransferEnv`.
- Use `render_prompt`, `score_transcript`, and `make_eval_record`.

Expected eval handoff:

```text
outputs/eval_results.jsonl
```

Validate:

```bash
.venv-eval/bin/python scripts/validate_handoffs.py --eval-jsonl outputs/eval_results.jsonl
```

Then summarize/plot:

```bash
.venv-eval/bin/python scripts/summarize_eval_results.py outputs/eval_results.jsonl --out outputs/eval_summary.md
.venv-eval/bin/python scripts/plot_eval_results.py outputs/eval_results.jsonl --out-dir outputs/plots
```

## Alex: Probe Lane

Setup:

```bash
uv venv .venv-probe --python 3.12
uv pip install --python .venv-probe/bin/python -r requirements/probe.txt
export HF_TOKEN="..."
```

No-model smoke:

```bash
.venv-probe/bin/python probes/test_probes.py
```

Base-only trace-smoke:

```bash
HF_HUB_DISABLE_XET=1 .venv-probe/bin/python -m probes.run_all \
  --model google/gemma-2-2b-it \
  --prompts data/shell_game_v1/shell_game_honest.sft.jsonl data/shell_game_v1/shell_game_deceptive.sft.jsonl \
  --stages base:none \
  --out-dir outputs/probes_trace_smoke \
  --device mps \
  --max-length 256 \
  --max-records 10 \
  --trace-smoke
```

This is pipeline validation only. It includes assistant traces and can leak
labels.

Eval-clean final probe after Vikas handoff:

```bash
.venv-probe/bin/python -m probes.run_all \
  --model google/gemma-2-2b-it \
  --prompts outputs/eval_results.jsonl \
  --stages default \
  --out-dir outputs/probes_eval_clean \
  --max-length 512
```

## Troubleshooting

If `torch` imports but has no `Tensor`, the environment is contaminated. Create
a fresh `uv venv`.

If `transformers` or `peft` fails on `markupsafe`, create a fresh `uv venv`.

If Gemma download fails:

- Confirm `HF_TOKEN` is set.
- Confirm the Gemma license is accepted for that Hugging Face account.
- Try `HF_HUB_DISABLE_XET=1` if downloads stall.

If `bitsandbytes` fails:

- Use it only on Linux/CUDA, usually Colab.
- Do not use it on MPS/macOS.

If a smoke run with honest + deceptive files says labels only contain one class,
pull latest `main`; `--max-records` should now limit per file, not globally.
