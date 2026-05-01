# Backlog

Concrete execution queue after the 2026-04-29 team call, through the
May 5 presentation and May 12 report. This complements `PLAN.md` and the
Mermaid flowchart in `README.md`; those explain the strategy, this file tracks
the next actions.

Status key: `ready`, `blocked`, `review`, `done`, `tabled`.
Effort key: `S` less than 1 hour, `M` half day, `L` full day, `XL` risky/multi-day.

## Now

| ID | Owner | Status | Effort | Task | Blocker | Next concrete action |
|---|---|---:|---:|---|---|---|
| NOW-A1 | Alex | ready | S | Keep frozen data reproducible | none | Run `python3 scripts/validate_handoffs.py --check-data` before using the dataset in new runs. |
| NOW-A2 | Alex | ready | S | Prepare eval result ingestion | waiting for Vikas JSONL only | Use `scripts/summarize_eval_results.py` and `scripts/plot_eval_results.py` on a sample or final eval JSONL. |
| NOW-A3 | Alex | ready | S | Lock slide/report evidence labels | none | Mark each plot/table as `final result`, `smoke test`, or `pending` before it goes into the deck. |
| NOW-R1 | Rithika | ready | M-L | Produce `control_corrupt` and `honest_corrupt` adapters | needs parent adapters in Colab/Drive | Run the cleaned corruption notebook from `control_sft` and `honest_sft` using the same deceptive SFT file. |
| NOW-V1 | Vikas/Alex | ready | S-M | Run final eval once checkpoints land | waiting for Rithika checkpoint paths | Use `scripts/eval_runner.py` over all available stages and write `outputs/eval_results.jsonl`. |

## Blocked

| ID | Owner | Status | Effort | Task | Blocker | Ready when |
|---|---|---:|---:|---|---|---|
| BLK-R1 | Rithika | blocked | M-L | Produce `control_corrupt` and `honest_corrupt` adapters | no new checkpoint handoff | `checkpoints/gemma_*_sft/final_adapter/` and `checkpoints/run_metadata.jsonl` exist or are shared. |
| BLK-V1 | Vikas | blocked | M | Produce scored shell-game eval JSONL | checkpoints absent | At least one model/checkpoint is runnable through `scripts/eval_runner.py`. |
| BLK-V2 | Vikas | blocked | M | Produce Python-transfer eval JSONL | checkpoints absent | Same as BLK-V1. |
| BLK-A1 | Alex | blocked | M | Final eval-clean layer migration plot | needs Vikas scored JSONL + Rithika adapters | `outputs/eval_results*.jsonl` and adapter paths are present. |
| BLK-A2 | Alex | blocked | S-M | Final behavior and transfer plots | needs Vikas scored JSONL | `scripts/summarize_eval_results.py` shows shell and py-transfer rows by stage. |

## Tabled

| ID | Owner | Status | Task | Why tabled | Untable trigger |
|---|---|---:|---|---|---|
| TBL-DPO | Team | tabled | DPO/PPO corruption arm | Not MVP for current deadline. | SFT-only results land early enough to justify stretch work. |

## Ready-When Inputs Land

| Input lands | Immediate command | Output |
|---|---|---|
| Rithika checkpoints | `python3 scripts/validate_handoffs.py --check-checkpoints` | Missing/present adapter matrix and metadata check. |
| Vikas eval JSONL | `python3 scripts/validate_handoffs.py --eval-jsonl outputs/eval_results.jsonl` | Schema and benchmark/stage coverage check. |
| Vikas eval JSONL | `python3 scripts/summarize_eval_results.py outputs/eval_results.jsonl --out outputs/eval_summary.md` | Markdown summary table for deck/report. |
| Vikas eval JSONL | `python3 scripts/plot_eval_results.py outputs/eval_results.jsonl --out-dir outputs/plots` | Behavior and transfer plot PNGs when fields are present. |
| Rithika adapters + Vikas eval JSONL | `python3 -m probes.run_all --model google/gemma-2-2b-it --prompts <eval-clean-jsonl> --stages default --out-dir outputs/probes_eval_clean` | Layer-migration artifacts. |

## Definition Of Done After The Call

- Data path validated: `data/shell_game_v1/` present and readable.
- PR #5 merged and eval runner available on `main`.
- Rithika checkpoint status known: exact paths or explicit "not ready".
- If no checkpoints: Alex can still show trace-smoke/base-only probe plan and risks.
- If eval JSONL lands: summary and plots generated from scripts in `scripts/`.
- Deck outline names which results are final vs smoke-test.

## Done

| ID | Owner | Status | Task | Evidence |
|---|---|---:|---|---|
| DONE-D1 | Alex | done | Freeze and track manual shell-game data v1 | `data/shell_game_v1/MANIFEST.md` and SFT JSONL files are tracked on `main`. |
| DONE-A1 | Alex | done | Probe scaffold merged | PR #3 merged, `probes/` on `main`. |
| DONE-A2 | Alex | done | Optional Anthropic generator merged | PR #4 merged, `dataset/generate.py` on `main`. |
| DONE-A3 | Alex | done | Review PR #5 | Review-request returned Changes Requested with Critical/High blockers. |
| DONE-A4 | Alex | done | Environment scaffold merged | PR #2 merged, `envs/` on `main`. |
| DONE-A5 | Alex | done | Base-only probe trace-smoke | `outputs/probes_trace_smoke/layer_migration_local-base-trace-smoke-apr29-n20.png` generated locally from 20 frozen SFT traces. |
| DONE-V1 | Vikas | done | Evaluation runner merged | PR #5 merged `scripts/eval_runner.py` and `scripts/smoke_test_envs.py` into `main`. |
