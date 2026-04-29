# Backlog

Concrete execution queue for the Wednesday 2026-04-29 working deadline and the
May 5 presentation. This complements `PLAN.md` and the Mermaid flowchart in
`README.md`; those explain the strategy, this file tracks the next actions.

Status key: `ready`, `blocked`, `review`, `done`, `tabled`.
Effort key: `S` less than 1 hour, `M` half day, `L` full day, `XL` risky/multi-day.

## Now

| ID | Owner | Status | Effort | Task | Blocker | Next concrete action |
|---|---|---:|---:|---|---|---|
| NOW-A1 | Alex | ready | S | Keep frozen data reproducible | none | Run `python3 scripts/validate_handoffs.py --check-data` before using the dataset in new runs. |
| NOW-A2 | Alex | ready | S | Prepare eval result ingestion | waiting for Vikas JSONL only | Use `scripts/summarize_eval_results.py` and `scripts/plot_eval_results.py` on a sample or final eval JSONL. |
| NOW-A3 | Alex | ready | M | Run probe smoke path | HF/Gemma access and local ML deps | Run `python3 probes/test_probes.py`; then use `python3 -m probes.run_all ... --stages base:none --trace-smoke` when model access is available. |
| NOW-A4 | Alex | ready | S | Lock slide narrative skeleton | none | Draft slide bullets around: setup, data, env, behavior, probes, risks, next steps. |
| NOW-T1 | Team | ready | S | Decide PR #2/#5 handling | Vikas feedback | At sync: merge/fix PR #2 first, rewrite or close PR #5 after that decision. |

## Blocked

| ID | Owner | Status | Effort | Task | Blocker | Ready when |
|---|---|---:|---:|---|---|---|
| BLK-R1 | Rithika | blocked | M-L | Produce `control_corrupt` and `honest_corrupt` adapters | no new checkpoint handoff | `checkpoints/gemma_*_sft/final_adapter/` and `checkpoints/run_metadata.jsonl` exist or are shared. |
| BLK-V1 | Vikas | blocked | M | Produce scored shell-game eval JSONL | PR #2/#5 unresolved and checkpoints absent | Env API is merged/settled and at least one model/checkpoint is runnable. |
| BLK-V2 | Vikas | blocked | M | Produce Python-transfer eval JSONL | PR #2/#5 unresolved and checkpoints absent | Same as BLK-V1. |
| BLK-A1 | Alex | blocked | M | Final eval-clean layer migration plot | needs Vikas scored JSONL + Rithika adapters | `outputs/eval_results*.jsonl` and adapter paths are present. |
| BLK-A2 | Alex | blocked | S-M | Final behavior and transfer plots | needs Vikas scored JSONL | `scripts/summarize_eval_results.py` shows shell and py-transfer rows by stage. |

## Tabled

| ID | Owner | Status | Task | Why tabled | Untable trigger |
|---|---|---:|---|---|---|
| TBL-P2 | Vikas/Alex | tabled | PR #2 `env/shell-game` | Need Vikas feedback before deciding merge vs supersede. | Vikas confirms whether PR #2 is still the intended env contract. |
| TBL-P5 | Vikas/Alex | tabled | PR #5 `vikas/evaluation_pipeline` | Review found Critical/High blockers and it depends on PR #2's intended scaffold. | PR #2 decision made; Vikas agrees to rewrite or hand branch to Alex. |
| TBL-DPO | Team | tabled | DPO/PPO corruption arm | Not MVP for current deadline. | SFT-only results land early enough to justify stretch work. |

## Ready-When Inputs Land

| Input lands | Immediate command | Output |
|---|---|---|
| Rithika checkpoints | `python3 scripts/validate_handoffs.py --check-checkpoints` | Missing/present adapter matrix and metadata check. |
| Vikas eval JSONL | `python3 scripts/validate_handoffs.py --eval-jsonl outputs/eval_results.jsonl` | Schema and benchmark/stage coverage check. |
| Vikas eval JSONL | `python3 scripts/summarize_eval_results.py outputs/eval_results.jsonl --out outputs/eval_summary.md` | Markdown summary table for deck/report. |
| Vikas eval JSONL | `python3 scripts/plot_eval_results.py outputs/eval_results.jsonl --out-dir outputs/plots` | Behavior and transfer plot PNGs when fields are present. |
| Rithika adapters + Vikas eval JSONL | `python3 -m probes.run_all --model google/gemma-2-2b-it --prompts <eval-clean-jsonl> --stages default --out-dir outputs/probes_eval_clean --hf-token "$HF_TOKEN"` | Layer-migration artifacts. |

## Definition Of Done For Tonight

- Data path validated: `data/shell_game_v1/` present and readable.
- PR #2/#5 disposition decided at sync, even if the answer is "close and rewrite".
- Rithika checkpoint status known: exact paths or explicit "not ready".
- If no checkpoints: Alex can still show trace-smoke/base-only probe plan and risks.
- If eval JSONL lands: summary and plots generated from scripts in `scripts/`.
- Deck outline names which results are final vs smoke-test.

## Done

| ID | Owner | Status | Task | Evidence |
|---|---|---:|---|---|
| DONE-D1 | Alex | done | Freeze manual shell-game data v1 | `data/shell_game_v1/MANIFEST.md` and SFT JSONL files exist locally. |
| DONE-A1 | Alex | done | Probe scaffold merged | PR #3 merged, `probes/` on `main`. |
| DONE-A2 | Alex | done | Optional Anthropic generator merged | PR #4 merged, `dataset/generate.py` on `main`. |
| DONE-A3 | Alex | done | Review PR #5 | Review-request returned Changes Requested with Critical/High blockers. |
