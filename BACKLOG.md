<!--
---
status: live
purpose: Concrete execution queue — RPT/EVD/UP items with status, owner, gates
workflow: report-week (post-May 5 talk → May 12 IEEE report)
last_updated: 2026-05-07
---
-->

# Backlog

Concrete execution queue for **The Slippery Slope** final project. Complements
`PLAN.md` and the Mermaid flowchart in `README.md` — those explain the strategy;
this file tracks the actions.

Status key: `ready`, `blocked`, `review`, `done`, `tabled`.
Effort key: `S` < 1 hour, `M` half day, `L` full day, `XL` risky/multi-day.

## Project Status

- **2026-05-05** — Class presentation **delivered in-class**. Live deck:
  Google Slides `1QJ4RJN7MqC4HIGwGPIoCaOD_irfPQTl9_nJGviKvc2s` (17 slides).
  Canonical PDF snapshot at `deliverables/The Slippery Slope - Big Data
  Final Project - RAV.pdf`. All 9 PRs merged. See `CHANGELOG.md` for the
  delivered-work activity log.
- **2026-05-12** — Final IEEE report due, 23:59 ET. Active lane.

## Now (Report Week — 2026-05-05 → 2026-05-12)

| ID | Owner | Status | Effort | Task | Next concrete action |
|---|---|---:|---:|---|---|
| RPT-1 | Alex | ready | L | Content-fill final IEEE report against Tier 2 canonical + mid-dose evidence | Day-by-day plan in personal class repo planning docs; report skeleton at `docs/archive/final-report-skeleton.md` (historical) + dose-response variant at `docs/final-report-skeleton-ieee-may12-dose-response.md`. |
| RPT-2 | Alex | ready | M | Add equivalence-gate + lexical-canary methodology beats to report § Interpretability Method | Strict equivalence gate caught CUDA generation-determinism break; lexical canary AUC drift across backends ≪ behavioral drift. Both surface as report-side methodology contributions. |
| RPT-3 | Alex | ready | S | Document class-flipped probe handling in report axis labels | Use "separability `max(AUC, 1-AUC)`" not raw AUC; some cells (e.g., `control_corrupt_middose_s1337__corrupt_reward` AUC 0.280 → sep 0.720) pass selection via class flip. Deck axes already use this language. |
| RPT-4 | Alex | ready | M | Surface bootstrap CIs in report numbers | `scripts/bootstrap_ci.py` is wired; preempt small-N skepticism. |
| RPT-5 | Alex | review | L | Scale parent SFT corpus 20 → 200-500 pairs + retrain both parents | Methodology gap: `experiments/sft_fix.py` hardcodes ~20 pairs per arm. Verify parent-stage gap (0.467 vs 0.353, p≈0.046 marginal) at expanded N. Decide whether to pursue before May 12 freeze. |
| EVD-1 | Alex | ready | M | Promote mid-dose evidence to `canonical_tier2_middose_<DATE>/` with sha256 manifest | Mirrors PR #9 + GCP variant evidence-tracking pattern. Cited in deck and report. |

## Stretch (Class Full only — do not let crowd Report Week)

| ID | Owner | Status | Effort | Task | Why |
|---|---|---:|---:|---|---|
| UP-A1 | Alex | ready | M | Activation steering at probe's best layer | Tests whether learned probe direction has causal effect, not just predictive signal. Strongest proposal-aligned stretch. Decide go/no-go for May 12 by 2026-05-08. |
| UP-A2 | Alex | review | M | Multi-task probe transfer review | Potentially impressive, but only valid if second task has enough rows + labels that are not prompt/template artifacts. Lower priority than UP-A1. |

## Tabled

| ID | Owner | Task | Why tabled | Untable trigger |
|---|---|---|---|---|
| TBL-DPO | Team | DPO/PPO corruption arm | Not MVP for May 12 deadline. SFT-only results landed; corruption induction proven via Tier 2. | Future paper-extension work; not in scope for this class deliverable. |
| TBL-PYTHIA | Team | Pythia-1.4B checkpoint-history stretch | Cut from MVP per `PLAN.md`. | Future paper-extension work. |

## Done

Pre-presentation execution queue. All items below were completed before or as part
of the 2026-05-05 in-class presentation delivery.

| ID | Owner | Task | Evidence |
|---|---|---|---|
| DONE-PRES | Team | **Class presentation delivered** | Google Slides `1QJ4RJN7MqC4HIGwGPIoCaOD_irfPQTl9_nJGviKvc2s`; canonical PDF at `deliverables/The Slippery Slope - Big Data Final Project - RAV.pdf`. Speaker ownership: Rithika 1-8 / Alex 9-13 / Vikas 14-17. |
| DONE-PR9 | Alex | Tier 2 canonical experiment | PR #9 merged 2026-05-04 at `785c99a`. Multi-seed corruption (3 seeds × 2 lineages), bootstrap CIs, lexical canary, layer-migration evidence under `deliverables/evidence/canonical_tier2_20260503_225150/`. |
| DONE-PR8 | Alex | Harden final eval and probe evidence | PR #8 merged 2026-05-03 at `5620307`. Bootstrap CI, lexical leakage canary, per-condition probe-input exports, resume-safe sharded shell-eval manifests. |
| DONE-MID | Alex | Mid-dose recipe sweep + L8 operating point | `outputs/recipe_middose_20260504/` (eval + probes); adapters at `checkpoints/tier2_recipe_middose_20260504/`. 250D / 250H × 0.20 epoch restored probe label balance: all 18 grouped 5-fold cells now train. |
| DONE-BATCH | Alex | Batch-eval equivalence test | MPS/fp32 batches 4/8/16 PASS strict parsed-label equivalence; best speedup batch 16 = 3.77×. CUDA non-quantized batch 4 FAILED equivalence at one row (`claimed_position` serial=2 vs batched=0); CUDA 4-bit not run after non-quantized failure (correct gate behavior). |
| DONE-PR7 | Team | Presentation + report scaffolds | PR #7 merged 2026-04-29; superseded by May 5 dose-response scaffolds. |
| DONE-PR6 | Team | Backlog and readiness scaffolds | PR #6 merged 2026-04-29. |
| DONE-PR5 | Vikas | Evaluation pipeline integrated | PR #5 merged 2026-04-30 at `54491b0`. `scripts/eval_runner.py` + `scripts/smoke_test_envs.py`. |
| DONE-PR4 | Alex | Optional Anthropic shell-game generator | PR #4 merged 2026-04-27. Class-leakage fix later landed via PR #8 (system blocks). |
| DONE-PR3 | Alex | Probe scaffold with shell-game data loader | PR #3 merged 2026-04-27. |
| DONE-PR2 | Alex | Shell-game and transfer-eval scaffold | PR #2 merged 2026-04-29. |
| DONE-D1 | Alex | Freeze + track manual shell-game data v1 + v2 | `data/shell_game_v1/MANIFEST.md` + `data/shell_game_v2/` tracked on `main`. |
