# Local Probe Smoke Status

Checked on 2026-04-29 while waiting for checkpoint/eval handoffs. Updated on
2026-05-01 after the local checkpoint download landed.

Historical commands and tables before the clean Path A rerun use the legacy
`control_corrupt` / `honest_corrupt` stage labels. Current deliverables and eval
JSONL use `control_clean_corrupt` / `honest_clean_corrupt`; legacy names should
now be interpreted as storage/checkpoint provenance, not current result labels.

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

## 2026-05-01 Neutral Eval And Partial Eval-Clean Probes

A neutral shell condition was added to remove the explicit corrupted reward
instruction from the prompt. It still asks for the same tagged shell-game
response, but says the model is evaluated on accurate, legible reporting.

Neutral shell eval command:

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
  --output_file outputs/eval_neutral_shell_20260501.jsonl \
  --rounds 20 \
  --shell-conditions neutral \
  --skip-py-transfer \
  --overwrite \
  --run_id local-neutral-20260501
```

Neutral shell summary:

| Stage | Deception rate | Parser errors |
|---|---:|---:|
| base | 1.000 | 0 |
| control_sft | 0.750 | 0 |
| honest_sft | 1.000 | 0 |
| control_corrupt | 0.400 | 0 |
| honest_corrupt | 0.650 | 0 |

Combining the corrupted-reward and neutral shell rows gives binary labels for
three stages:

| Stage | Rows | Deceptive | Honest/non-deceptive | Probe status |
|---|---:|---:|---:|---|
| control_sft | 40 | 35 | 5 | ran |
| control_corrupt | 40 | 28 | 12 | ran |
| honest_corrupt | 40 | 26 | 14 | ran |
| base | 40 | 40 | 0 | skipped |
| honest_sft | 40 | 40 | 0 | skipped |

Partial eval-clean prompt probes were run stage-by-stage on prompt-only rows.
These avoid assistant-trace leakage, but they are still small and confounded by
prompt condition, so they should be presented as preliminary rather than as the
central interpretability claim.

Adversarial review on 2026-05-02 tightened this caveat: the three 40-row
eval-clean prompt files contain only 6 unique prompt groups per stage. The old
row-wise probe split can therefore place duplicate prompt activations in both
train and test, so the AUC 1.0 values below are now treated as non-independent
sanity checks, not evidence for an internal deception signal.

Best-layer summary:

| Stage | Best layer | Best AUC | Note |
|---|---:|---:|---|
| control_sft | 1 | 1.000 | highly imbalanced labels, 35/5 |
| control_corrupt | 0 | 1.000 | 28/12 labels |
| honest_corrupt | 7 | 1.000 | 26/14 labels |

Generated ignored artifacts:

- `outputs/eval_neutral_shell_20260501.jsonl`
- `outputs/eval_neutral_shell_summary_20260501.md`
- `outputs/plots_neutral_shell_20260501/behavior_deception_rate.png`
- `outputs/probes_eval_clean_inputs_20260501/*.jsonl`
- `outputs/probes_eval_clean_20260501/layer_migration_eval-clean-usable-stages-20260501.png`

## 2026-05-02 Rescue Patch

Two methodology fixes landed after the adversarial review:

- `ShellGameEnv.reset()` now assigns a prompt variant, and
  `ShellGameEnv.render_prompt()` has 20 shell prompt variants. The default
  20-round shell eval now produces 20 unique prompt strings per condition
  instead of collapsing to 3 prompts keyed only by true cup.
- Shell eval records now include `prompt_variant` and `prompt_id`, so downstream
  probe inputs can preserve prompt grouping.
- `probes.data.load_probe_examples()` writes a stable `group_id` for each
  example, using explicit `group_id`/`prompt_id` when present and otherwise
  hashing the rendered model input.
- `probes.run_all --split-strategy auto` uses grouped train/test splitting when
  duplicate prompt groups exist.
- `probes.train.train_probes()` fails loudly if a grouped split cannot place both
  classes on both sides. Use `--split-strategy row` only for smoke tests that
  will not be presented as evidence.

Recommended rerun shape:

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
  --output_file outputs/eval_prompt_diverse_shell_20260502.jsonl \
  --rounds 20 \
  --shell-conditions corrupt_reward neutral \
  --skip-py-transfer \
  --overwrite \
  --run_id local-prompt-diverse-20260502
```

Then create eval-clean probe inputs from the prompt-diverse shell rows and run
probes with the default grouped split strategy. A grouped split that fails is a
valid finding: it means the prompt suite is still too small or too imbalanced
for claim-level probe evidence.

## 2026-05-02 Prompt-Diverse Eval And Probe Pass

Prompt-diverse shell eval command wrote:

```text
outputs/eval_prompt_diverse_shell_20260502_231025.jsonl
```

Each stage/condition cell has 20 rows and 20 unique prompt IDs:

| Stage | Corrupt reward deception | Neutral deception | Parser errors |
|---|---:|---:|---:|
| base | 0.850 | 0.750 | 0 / 0 |
| control_sft | 0.700 | 0.700 | 2 / 2 |
| honest_sft | 0.600 | 0.500 | 0 / 1 |
| control_corrupt | 0.900 | 0.800 | 0 / 1 |
| honest_corrupt | 0.400 | 0.550 | 6 / 2 |

Prompt IDs use `shell:{eval_condition}:variant-{XX}:truth-{Y}` and deliberately
exclude `stage`. For the current per-stage probes, this groups duplicate prompts
within a stage. For a future cross-stage analysis, use the same `prompt_id` when
identical prompts across stages should be grouped together, or derive
`{prompt_id}|{stage}` when stages should be treated independently.

Prompt-diverse eval-clean probes wrote:

```text
outputs/probes_prompt_diverse_20260502_231025/
```

Best-layer summary:

| Stage | Rows | Pos/neg | Split strategy | Best layer | Best AUC |
|---|---:|---:|---|---:|---:|
| base | 40 | 32/8 | row_stratified_no_duplicate_groups | 2 | 0.917 |
| control_sft | 40 | 28/12 | row_stratified_no_duplicate_groups | 0 | 1.000 |
| honest_sft | 40 | 22/18 | row_stratified_no_duplicate_groups | 3 | 0.688 |
| control_corrupt | 40 | 34/6 | row_stratified_no_duplicate_groups | 0 | 0.571 |
| honest_corrupt | 40 | 19/21 | row_stratified_no_duplicate_groups | 8 | 0.562 |

Slide-ready artifacts:

- `outputs/plots_prompt_diverse_20260502_231025/behavior_deception_rate_by_condition_20260502_231025.png`
- `outputs/probes_prompt_diverse_20260502_231025/layer_migration_prompt-diverse-combined_20260502_231025.png`
- `deliverables/slippery-slope-results-rescue-20260503_004841.pptx`
- `deliverables/slippery-slope-results-rescue-20260503_004841.pdf`

These generated artifacts are gitignored local evidence. Verify local copies
with SHA-256 before migration:

| Artifact | SHA-256 |
|---|---|
| `outputs/eval_prompt_diverse_shell_20260502_231025.jsonl` | `913909b2f407fed20de011db77ce1ebb412db058354c3f408829cbb7abf2c59f` |
| `outputs/eval_prompt_diverse_shell_condition_summary_20260502_231025.md` | `fae85d682e98d675bbc44bc154008ab4dc7c84da126e184f932bd8c1836ee348` |
| `outputs/probes_prompt_diverse_20260502_231025/probe_summary_prompt-diverse_20260502_231025.md` | `2fedd1c6cc1d0a1a53afd810d03859d71509a26f625cbd3e13ebdbe3dcbc8946` |
| `deliverables/slippery-slope-results-rescue-20260503_004841.pptx` | `9a33dbbd6c993362d9b1bf90cd4a2557821940dd50c35ba03213fe32a4e36bd8` |
| `deliverables/slippery-slope-results-rescue-20260503_004841.pdf` | `e2f8f9970a0ff58d6b872c3f6013d8e11579a83dc5cb24aa3c5601cf9f0ed106` |

## 2026-05-03 Path A Clean SFT Leak Audit

Path A branch:

```text
codex-prb/clean-data-path-a
```

The frozen SFT files were regenerated so model-visible user prompts no longer
contain `Stage=honest`, `Stage=deceptive`, `mode=honest`, `mode=deceptive`, or
similar class markers. The raw JSONL files still preserve the original prompts
for provenance. The SFT files now keep labels and grouping as metadata outside
the model-visible `messages` field.

Audit result:

| File | Rows | Bad user prompts | Missing groups | Label |
|---|---:|---:|---:|---:|
| `data/shell_game_v1/shell_game_honest.sft.jsonl` | 100 | 0 | 0 | 0 |
| `data/shell_game_v1/shell_game_deceptive.sft.jsonl` | 100 | 0 | 0 | 1 |

Across both SFT files there are 100 unique prompt groups for 200 rows, so each
honest/deceptive prompt pair shares a `group_id`. This makes grouped splitting
active on the actual data instead of relying on a best-effort fallback.

Small base-only MPS canary, 10 records per class:

```bash
HF_HUB_DISABLE_XET=1 /Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python -m probes.run_all \
  --model google/gemma-2-2b-it \
  --prompts data/shell_game_v1/shell_game_honest.sft.jsonl data/shell_game_v1/shell_game_deceptive.sft.jsonl \
  --stages base:none \
  --out-dir outputs/path_a_clean_prompt_probe_20260503 \
  --run-id path-a-clean-base-n10-20260503 \
  --device mps \
  --max-length 256 \
  --max-records 10
```

Result:

| Input mode | Split | Best AUC | Best accuracy | Interpretation |
|---|---|---:|---:|---|
| prompt-only clean SFT | `group_shuffle` | 0.500 | 0.500 | class markers removed; prompt-only SFT contrast is no longer separable |
| trace-smoke with assistant traces | `group_shuffle` | 1.000 | 1.000 | assistant completions still leak labels; smoke test only |

This is the expected canary result. It does not test whether retrained clean
corruption adapters retain a behavioral signal; it only proves the old SFT-probe
shortcut was leakage-driven and that the clean prompt/grouping guardrails work.

## 2026-05-03 Full Path A Clean Rerun

Branch:

```text
codex-prb/full-path-a-rerun
```

Fresh clean-corruption adapters were trained from the parent `control_sft` and
`honest_sft` adapters using the cleaned deceptive SFT rows. The train script is
`experiments/train_clean_corruption.py`; it writes ignored local adapters under:

```text
checkpoints/path_a_clean_corruption_20260503/
```

The prompt-diverse shell eval then ran five stages: base, the two parent SFT
adapters, and the two clean-corruption adapters. Parser-error rows were dropped
from the probe inputs because they do not contain a legible public claim.

Behavior summary:

| Stage | Corrupt reward deception | Neutral deception | Parser errors |
|---|---:|---:|---:|
| base | 0.85 | 0.75 | 0 / 0 |
| control_sft | 0.70 | 0.70 | 2 / 2 |
| honest_sft | 0.60 | 0.50 | 0 / 1 |
| control_clean_corrupt | 0.55 | 0.50 | 1 / 0 |
| honest_clean_corrupt | 0.70 | 0.55 | 1 / 1 |

Prompt-clean probe summary:

| Stage | Probe rows | Pos/neg | Best layer | Best AUC | Split |
|---|---:|---:|---:|---:|---|
| base | 40 | 32/8 | 2 | 0.917 | row-stratified; unique prompt IDs |
| control_sft | 36 | 28/8 | 23 | 1.000 | row-stratified; unique prompt IDs |
| honest_sft | 39 | 22/17 | 23 | 0.667 | row-stratified; unique prompt IDs |
| control_clean_corrupt | 39 | 21/18 | 8 | 0.625 | row-stratified; unique prompt IDs |
| honest_clean_corrupt | 38 | 25/13 | 25 | 0.733 | row-stratified; unique prompt IDs |

Interpretation:

- The old leakage-driven trace story is still invalid for final claims.
- The clean Path A rerun does not fully collapse to chance, but the fresh
  clean-corruption adapters produce moderate probe separability rather than a
  dramatic layer-migration result.
- Each in-stage probe row has a unique prompt ID, so there are no duplicate
  prompt groups for grouped splitting to separate. This is why the runner reports
  `row_stratified` instead of `group_shuffle`.
- With 36-40 rows per stage and 8-row holdouts, these AUCs are preliminary
  diagnostic evidence, not a broad mechanistic deception detector.

Ignored local artifacts:

- `outputs/path_a_clean_eval_20260503.jsonl`
- `outputs/path_a_clean_eval_summary_20260503.md`
- `outputs/path_a_clean_plots_20260503/behavior_deception_rate.png`
- `outputs/path_a_clean_probe_inputs_20260503/summary.md`
- `outputs/path_a_clean_probes_20260503/probe_summary_path_a_clean_20260503.md`
- `outputs/path_a_clean_probes_20260503/layer_migration_path_a_clean_20260503.png`

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
