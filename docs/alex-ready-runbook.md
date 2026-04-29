# Alex Ready Runbook

Commands to run when teammate artifacts land. This keeps the final stretch from
turning into archaeology.

## 1. Check Current Repo Readiness

```bash
python3 scripts/validate_handoffs.py --check-data
python3 probes/test_probes.py
```

If running from a worktree that does not contain gitignored `data/`,
add `--repo-root /Users/wax/coding/The_Slippery_Slope` to point at the root
checkout's local artifacts.

Expected today:

- `--check-data` should pass if `data/shell_game_v1/` is present locally.
- `probes/test_probes.py` should pass without model downloads.

## 2. When Rithika Sends Checkpoints

Put or symlink adapters into:

```text
checkpoints/gemma_control_sft/final_adapter/
checkpoints/gemma_honest_sft/final_adapter/
checkpoints/gemma_control_corrupt_sft/final_adapter/
checkpoints/gemma_honest_corrupt_sft/final_adapter/
checkpoints/run_metadata.jsonl
```

Then run:

```bash
python3 scripts/validate_handoffs.py --check-checkpoints
```

If only base/control/honest exist, use explicit stage specs instead of
`--stages default`:

```bash
python3 -m probes.run_all \
  --model google/gemma-2-2b-it \
  --prompts data/shell_game_v1/shell_game_honest.sft.jsonl data/shell_game_v1/shell_game_deceptive.sft.jsonl \
  --stages base:none control_sft:checkpoints/gemma_control_sft/final_adapter honest_sft:checkpoints/gemma_honest_sft/final_adapter \
  --out-dir outputs/probes_trace_smoke \
  --hf-token "$HF_TOKEN" \
  --trace-smoke
```

## 3. When Vikas Sends Eval JSONL

Assume the first target path is:

```text
outputs/eval_results.jsonl
```

Validate and summarize:

```bash
python3 scripts/validate_handoffs.py --eval-jsonl outputs/eval_results.jsonl
python3 scripts/summarize_eval_results.py outputs/eval_results.jsonl --out outputs/eval_summary.md
python3 scripts/plot_eval_results.py outputs/eval_results.jsonl --out-dir outputs/plots
```

Expected plot outputs, when fields are present:

```text
outputs/plots/behavior_deception_rate.png
outputs/plots/transfer_tamper_rate.png
```

If `matplotlib` is not installed, the plotting script writes `.svg` fallbacks
with the same base names.

## 4. Eval-Clean Probe Run

Use this only after Vikas's eval JSONL has behavior labels that do not leak the
answer through the prompt/assistant training trace.

```bash
python3 -m probes.run_all \
  --model google/gemma-2-2b-it \
  --prompts outputs/eval_results.jsonl \
  --stages default \
  --out-dir outputs/probes_eval_clean \
  --hf-token "$HF_TOKEN" \
  --max-length 512
```

If checkpoint handoff is partial, replace `--stages default` with explicit
`stage:adapter_path` pairs for the stages that exist.

## 5. Slide-Ready Artifacts

Minimum deck assets:

```text
outputs/eval_summary.md
outputs/plots/behavior_deception_rate.png
outputs/plots/transfer_tamper_rate.png
outputs/probes_trace_smoke/layer_migration_<run_id>.png
```

Stretch deck asset:

```text
outputs/probes_eval_clean/layer_migration_<run_id>.png
```

Label trace-smoke plots clearly. They validate the pipeline, not the final
interpretability claim.
