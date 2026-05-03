# Alex Ready Runbook

Commands to run when teammate artifacts land. This keeps the final stretch from
turning into archaeology.

## 1. Check Current Repo Readiness

```bash
python3 scripts/validate_handoffs.py --check-data
python3 probes/test_probes.py
```

If running from a stale worktree that does not contain tracked `data/`,
pull/rebase first or add `--repo-root /Users/wax/coding/The_Slippery_Slope`
to point at the synced root checkout.

Expected today:

- `--check-data` should pass if `data/shell_game_v1/` is present in the checkout.
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

The corrupt adapter directory names are legacy handoff paths. For the clean Path
A rerun, label the eval stages as `control_clean_corrupt` and
`honest_clean_corrupt` so artifacts match the current report/deck tables. Do
not pass the legacy stage labels in `--stages`; only the storage paths retain
the old names.

Then run:

```bash
python3 scripts/validate_handoffs.py --check-checkpoints
```

If the adapters stay in Google Drive/Colab instead of local Git checkout, run
the real eval in Colab after mounting Drive:

```bash
python3 scripts/eval_runner.py \
  --model_id google/gemma-2-2b-it \
  --adapters \
    base \
    /content/drive/MyDrive/Big_Data_Analytics_Final_Project/checkpoints/gemma_control_sft/final_adapter \
    /content/drive/MyDrive/Big_Data_Analytics_Final_Project/checkpoints/gemma_honest_sft/final_adapter \
    /content/drive/MyDrive/Big_Data_Analytics_Final_Project/checkpoints/gemma_control_corrupt_sft/final_adapter \
    /content/drive/MyDrive/Big_Data_Analytics_Final_Project/checkpoints/gemma_honest_corrupt_sft/final_adapter \
  --stages base control_sft honest_sft control_clean_corrupt honest_clean_corrupt \
  --output_file outputs/eval_results.jsonl \
  --rounds 20 \
  --quantize \
  --overwrite
```

Bring back only `outputs/eval_results.jsonl`, `outputs/eval_summary.md`, and
plot files. Do not upload adapter binaries to GitHub.

If only base/control/honest exist, use explicit stage specs instead of
`--stages default`:

```bash
python3 -m probes.run_all \
  --model google/gemma-2-2b-it \
  --prompts data/shell_game_v1/shell_game_honest.sft.jsonl data/shell_game_v1/shell_game_deceptive.sft.jsonl \
  --stages base:none control_sft:checkpoints/gemma_control_sft/final_adapter honest_sft:checkpoints/gemma_honest_sft/final_adapter \
  --out-dir outputs/probes_trace_smoke \
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
  --max-length 512 \
  --split-strategy auto
```

If checkpoint handoff is partial, replace `--stages default` with explicit
`stage:adapter_path` pairs for the stages that exist.

`--split-strategy auto` keeps duplicate prompt groups together when they exist.
If it fails to find a grouped split with both behavior classes on both sides,
the prompt suite is not yet strong enough for a claim-level probe plot.

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

## PPTX Lock

- Hard checkpoint: 2026-05-04 18:00 local.
- After lock: only typo/text fixes inside Keynote; no figure swaps or slide
  reorders.
- Final filename pattern: `deliverables/slippery-slope-final-<YYYYMMDD>.pptx`.
- Verify: open the file once after lock; record the timestamp here.
- May 5 PPTX uses the Phase 0 no-CI layer-migration plot. Phase 1 CI plots land
  in the report; an optional post-presentation deck copy may add CI bars later.

Deck dry-run:

- Target: <=12 minutes.
- Status: not yet timed.
