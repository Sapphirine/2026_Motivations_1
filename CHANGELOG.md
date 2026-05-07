<!--
---
status: live
purpose: Activity log + version history — meetings, decisions, experiments, code changes
workflow: project-lifetime
last_updated: 2026-05-07
---
-->

# Changelog

All notable changes and activity for **The Slippery Slope** final project. Semantic versioning (`vX.Y.Z — YYYY-MM-DD — <slug>`); every commit bumps at least the patch number. Doubles as an activity log — meetings, key decisions, and experimental results alongside code changes.

## [Unreleased]

Entries accumulate here until the next version bump.

Audit pass — squash + frontmatter + archive sweep on top of the prior
post-presentation cleanup. After this commit, every live doc carries
`status / purpose / workflow / last_updated` frontmatter; archive
folders are gitignored and untracked but preserved on disk.

### Audit pass (2026-05-07) — README rewrite + PLAN move + BACKLOG cleanup

- **README rewrite.** Replaced ~410 lines of dated scaffolding (stale
  Project Status mermaids, "fixes vs v1" detail, notebook-specific
  section, teammate-name callouts) with a concise project entry point:
  overview, single current pipeline mermaid, repo layout, quick-start
  commands (train / evaluate / probe / validate), status line, compute
  table, model assets, references. Added Acknowledgments section
  acknowledging AI-tool use during development. Detailed lane / handoff
  content lives in `docs/team-runbook.md`; v1 → v2 history lives in
  CHANGELOG entries.
- **PLAN.md moved** to personal class repo
  (`Final_Project/planning/archive/team-repo-PLAN.md`). Was archival —
  pre-presentation 5-day plan with deadlines past. Current report-week
  execution lives in BACKLOG.md.
- **BACKLOG header refreshed** — drops PLAN.md reference; flags active
  vs archived report skeleton paths.

### Audit pass (2026-05-07) — squash + frontmatter + archive sweep, prior round

- **Squash:** collapsed 3 prior commits (`c4f00c4` May 5 scaffolds,
  `d236272` post-presentation cleanup, `734e4bd` `.cgcignore` sync)
  into a single commit `b8fd356` for a cleaner main log. The BLOCKED
  Tier 2 GCP commit `0e30ba2` is left separate.
- **Frontmatter** added to all 10 live docs (4 root + 6 `docs/`).
  Shape: `status / purpose / workflow / last_updated`. Existing
  frontmatter on the May 5 dose-response trio preserved + extended
  (added `purpose`, `workflow`, `last_updated`; refreshed `status`
  from `current_scaffold` → `live`).
- **`docs/archive/` gitignored + untracked** (`git rm --cached`).
  12 archived docs preserved on disk; not visible in git history
  going forward. Mirrors the existing pattern for
  `deliverables/archive/` and `deliverables/drafts/`.
- **Path A evidence** at `deliverables/evidence/path_a_clean_20260503/`
  + `deliverables/path_a_clean_20260503.sha256` gitignored + untracked.
  Path A was superseded by canonical Tier 2 (May 5 deck §
  "Do Not Use As Headline Evidence"); kept locally for audit only.

### Post-presentation cleanup sweep — squashed into a single commit covering
the team-repo half of the OPS-004 cleanup (the personal class repo got
its own series; this entry tracks team-repo changes only).

### Added

- Canonical PDF snapshot of the delivered presentation at
  `deliverables/The Slippery Slope - Big Data Final Project - RAV.pdf`
  (downloaded from canonical Google Slides
  `1QJ4RJN7MqC4HIGwGPIoCaOD_irfPQTl9_nJGviKvc2s` after May 5 in-class
  delivery).

### Changed

- `BACKLOG.md`: refreshed to post-presentation state. New "Project
  Status" header (presentation delivered May 5; report due May 12).
  Pre-presentation execution queue (NOW + BLK items) collapsed to a
  `Done` table rolling up the 9 merged PRs + mid-dose recipe sweep +
  batch-eval equivalence test + presentation delivery. Active "Now"
  section refocused on Report Week (RPT-1..5 + EVD-1) and Stretch
  (UP-A1, UP-A2).
- `PLAN.md`: added "Project Status (2026-05-05)" header noting
  delivery. Strategic body retained as the original spine.
- `README.md`: 3 path references updated mechanically to point at
  `docs/archive/` with historical-context notes.
- `.gitignore`: added `deliverables/archive/` (companion to the existing
  `deliverables/drafts/` rule).

### Removed

- Migrated 3 pre-PR-#3 starter notebooks out of `notebooks/` to the
  personal class repo at
  `~/coding/Classes/EECS-E6895/Final_Project/notebooks_archive/team_repo_pre_pr3/`
  (`Big_Data_Analytics_Final_Project3.ipynb` + 2 early Alex iterations;
  ~21k lines total). These were archeology, not load-bearing for the
  PR-#3+ module split (`experiments/`, `probes/`, `envs/`, `scripts/`,
  `dataset/`). `notebooks/sft_pipeline_v2_2026-04-24.ipynb` is retained
  — it is the Colab-runnable SFT pipeline still referenced by README as
  Rithika's iteration path.
- Untracked `deliverables/figures/` (PR #7 era PNGs:
  `behavior_deception_rate.png`, `layer_migration.png`, `pipeline.png`).
  Superseded by `deliverables/evidence/canonical_tier2_*/eval/` and
  `.../probes/` figures. PNGs moved to gitignored
  `deliverables/archive/figures_pr7/`.

### Archived to `docs/archive/`

- `final-presentation-draft.md` (explicit `status: superseded`).
- `pr2-pr5-decision-memo.md` (PRs long-merged).
- `alex-ready-runbook.md` (April 29 runbook; presentation done).
- `execution-plan.md` (April 29 post-team-call execution plan; all PRs
  done).
- `local-probe-smoke-status.md` (April 29 smoke status; results landed
  via PR #8 + #9).
- `final-prep-tier01.md` + `final-prep-tier01_spec.md` (PR #8 plan +
  spec; merged) per `claude/rules/plans.md` § Post-Merge convention.
- `final-prep-tier02.md` + `final-prep-tier02_spec.md` (PR #9 plan +
  spec; merged) per same convention.
- `deck-skeleton.md` + `final-report-skeleton.md` (early scaffolds;
  superseded by the May 5 dose-response trio in `docs/`).
- `pipeline.mmd` (moved out of `docs/architecture/`; pipeline diagram
  unreferenced from active docs after the v9 deck rebuilt slide 6 with
  native python-pptx shapes; preserved as historical reference).

### Deliverables / drafts

- Older delivery drafts moved to `deliverables/archive/` (gitignored
  alongside `deliverables/drafts/`). Files preserved on disk for
  reference; not in tracked content.

### Documentation refs (mechanical)

- Dose-response scaffolds (`docs/deck-skeleton-may5-dose-response.md`,
  `docs/final-presentation-draft-may5-dose-response.md`,
  `docs/final-report-skeleton-ieee-may12-dose-response.md`): paths to
  newly-archived planning docs in the personal class repo updated to
  `Final_Project/planning/archive/...`; reference to
  `EECS6895-AdvancedAI-Final-Project-Info.pdf` updated to its new
  `Final_Project/research_sources/` location; reference to the
  superseded Updated.pptx visual-look anchor noted as
  `Final_Project/design/archive/...`.

## [v0.1.19] — 2026-05-04 — may5-dose-response-scaffolds

### Added
- Added current May 5 / May 12 dose-response scaffolds for the final deck,
  speaker-note presentation draft, and IEEE report.

### Changed
- Marked the older deck/report/presentation scaffolds as superseded by the
  PR #9 high-dose, pre-mid-dose L8 cut so future edits do not reuse stale
  Path A or high-dose-only framing as current truth.

## [v0.1.18] — 2026-05-04 — final-prep-tier02-canonical

### Added
- Added Tier 2 corpus scaling, held-out-family eval splitting, activation-cache
  extraction, true in-family-to-held-out transfer probes, seed aggregation, and
  seed-band layer-migration plotting helpers for the canonical experiment.
- Added backlog upgrade pins for activation steering at the probe's best layer
  and a later review of multi-task probe transfer once valid second-task
  evidence is available.
- Added resume-safe sharded shell eval manifests, deterministic prompt seeds,
  prompt-family metadata, bootstrap CI tooling, lexical leakage canary tooling,
  and per-condition probe-input exports for final-project evidence hardening.
- Added committed Path A clean figure/evidence snapshots under `deliverables/`
  so final deck/report references no longer depend on sibling worktrees.
- Added `experiments/train_clean_corruption.py` for the full Path A rerun:
  starting from parent SFT adapters, train fresh corruption LoRA adapters
  on the leakage-controlled shell-game SFT data.
- Added reproducible eval-to-probe conversion and probe-summary scripts for
  prompt-only Path A artifacts.
- Generated prompt-diverse shell eval, plot, eval-scored probe artifacts, and a
  timestamped repair deck/PDF for the May 5 presentation.
- Added 20 shell prompt variants plus `prompt_id`/`prompt_variant` metadata so
  default 20-round shell evals no longer collapse to three repeated cup-only
  prompts.
- Added prompt-group metadata and grouped probe train/test splitting so duplicate
  prompt activations cannot silently leak across probe train/test splits.
- Added a neutral shell-eval prompt condition to `ShellGameEnv` and
  `scripts/eval_runner.py`, plus a `--skip-py-transfer` option for shell-only
  probe-label runs.
- Added `docs/final-presentation-draft.md`, a slide-by-slide draft that frames
  current results, limitations, and provisional probe analysis for the May 5
  presentation.

### Changed
- Extended `experiments/train_clean_corruption.py` with deterministic seed selection,
  public output-stage naming, overwrite protection, dataset hashes, parent
  adapter hashes, and final adapter metadata for Tier 2 multi-seed runs.
- Updated behavior/probe plot color maps and summaries for canonical
  seed-suffixed corruption stage names and condition-aware behavior tables.
- Removed AI-tooling and internal-process references from grader-facing
  surfaces.
- Extended probe training and summaries with balanced accuracy, persisted
  record IDs, split manifests, per-layer test predictions, k-fold support, and
  explicit degenerate-cell handling for per-condition analysis.
- Regenerated the lexical baseline with `--kfold 5` and surfaced the resulting
  small-sample/class-flip caveats in the final report/deck evidence trail.
- Rebuilt `data/shell_game_v1/*.sft.jsonl` with class-neutral user prompts and
  explicit label/group metadata, preserving raw prompt-labelled JSONL only as
  provenance.
- Removed stored user-prompt class leakage from the optional Anthropic generator
  by moving honest/deceptive instructions into non-stored system blocks.
- Expanded the deck/report skeletons with a pipeline figure, artifact-backed
  result slots, related-work paragraphs, and methods alternatives so the May 5
  materials no longer ship placeholder-only rubric sections.
- Reframed public presentation docs around the repair methodology: initial
  ceiling results are the pre-repair baseline, while prompt diversity and
  grouped splitting are the implemented fix for stronger final evidence.
- Documented the 2026-05-01 Drive checkpoint handoff status, including which
  adapter folders are present, what was validated without downloading binaries,
  and where to run the final load/eval test if checkpoints stay in Colab.
- Stopped tracking stale generated `outputs/*.jsonl` files while explicitly
  allowing the small checkpoint `run_metadata.jsonl` handoff file.
- Updated checkpoint validation to accept non-local Colab provenance paths when
  the matching local adapter directories are present.
- Recorded the 2026-05-01 local five-stage eval and all-checkpoint trace-smoke
  results, including the shell deception ceiling issue and eval-scored probe
  limitation.
- Replaced the single status diagram with high-level and detailed Mermaid
  project-flow diagrams covering the project from proposal through final report,
  with current done/in-progress/not-started/blocked/risk coloring.
- Renamed the companion status doc to `docs/execution-plan.md` and removed
  stale date-specific wording from current planning surfaces.
- Recorded neutral shell eval results and partial eval-scored prompt probes for
  the three stages with both behavior classes.

### Validated
- Added smoke coverage for condition-aware eval summaries, family splitting,
  transfer-probe integrity checks, v2 corpus generation, seed aggregation, and
  the new canonical plotting helper.
- Ran the full Path A local rerun across five stages. Corruption
  adapters trained successfully, prompt-diverse shell eval produced both classes
  after dropping parser errors, and prompt-only probes reached moderate
  corruption AUCs rather than the trace-smoke label-leakage shortcut.
- Ran a Path A base-only leak canary: prompt-only SFT probes drop to AUC
  0.5 under grouped splitting, while trace-smoke with assistant completions still
  reaches AUC 1.0.

## [v0.1.17] — 2026-04-30 — post-call-completion-plan

### Added
- `scripts/eval_runner.py`: End-to-end evaluation script that loads model checkpoints (adapters), runs the shell game and Python transfer benchmarks, and writes results to JSONL. Includes multi-device support (CUDA, MPS, CPU) and auto-merging of LoRA adapters.
- `scripts/smoke_test_envs.py`: Unit tests for `ShellGameEnv` and `PythonTransferEnv` to verify scoring logic for honest, deceptive, and tampered responses.

### Changed
- Replaced the sync-call flow with a post-call completion flow in `README.md` and `docs/execution-plan.md`, showing done items, remaining handoffs, final artifact generation, and fallback risks through presentation/report completion.
- Updated `BACKLOG.md` now that PR #5 is merged; eval runner work is done and final eval is blocked only on checkpoint availability.
- Refreshed `docs/team-runbook.md` and `docs/deck-skeleton.md` to remove stale PR #5 blocker wording.

## [v0.1.16] — 2026-04-29 — team-uv-runbook

### Added
- Added `docs/team-runbook.md` with shared `uv venv` setup, token hygiene, lane-specific commands for Rithika/Vikas/Alex, and explicit shell-game SFT data usage guidance.
- Added lightweight requirements manifests for base scripts, eval, probes, training, and Colab/CUDA training.

## [v0.1.15] — 2026-04-29 — probe-smoke-readiness

### Changed
- Updated the probe runner to read `HF_TOKEN` from the environment by default and removed token-bearing CLI examples from docs.
- Changed probe `--max-records` to limit rows per input file so honest/deceptive smoke runs stay class-balanced.
- Recorded the successful base-only trace-smoke run and updated deck/report/backlog status placeholders accordingly.

## [v0.1.14] — 2026-04-29 — dataset-artifact-docs

### Changed
- Explained each `data/shell_game_v1/` artifact in the manifest and manual-generation docs, and removed stale wording that described the frozen dataset as local/gitignored.
- Updated `experiments/prepare_shell_game_data.py` so regenerated manifests preserve those artifact descriptions.
- Refreshed `BACKLOG.md` now that PR #2 and the frozen dataset are both on `main`.

## [v0.1.13] — 2026-04-29 — shell-game-data-tracking

### Added
- Tracked the frozen shell-game raw, SFT, manifest, and review artifacts under `data/` so teammates can pull the already-generated 100 honest + 100 deceptive examples from `main`.

### Changed
- Updated `.gitignore` to keep the current shell-game dataset versioned while continuing to ignore large/local ML artifacts by default.

## [v0.1.12] — 2026-04-29 — env-eval-scaffold

### Added
- `envs/` module with `ShellGameEnv`, `PyTransferEnv`, shared JSONL writer, name/number cup-claim parsing, and eval-record builders extending the manual SFT JSONL shape with eval-specific fields.

### Changed
- Shell-game eval prompts avoid `honest` / `deceptive` stage labels so downstream behavior labels come from parsed model claims rather than prompt leakage.

## [v0.1.11] — 2026-04-29 — review-polish

### Changed
- Tightened the presentation/report scaffold after cross-agent review by clarifying trace-smoke limitations, base-vs-LoRA stage semantics, and current-result status placeholders.
- Expanded `examples/sample_eval_results.jsonl` so the synthetic fixture covers all five planned model stages across shell and Python-transfer benchmarks.
- Clarified the local probe environment repair note to prefer a clean environment and record resolved dependency versions after a successful smoke run.

## [v0.1.10] — 2026-04-29 — presentation-writing-scaffold

### Added
- `docs/deck-skeleton.md` and `docs/final-report-skeleton.md` to unblock presentation/report drafting while checkpoint and eval handoffs are pending.
- `docs/pr2-pr5-decision-memo.md` with a concise sync-ready framing for the PR #2 / PR #5 decision.
- `docs/local-probe-smoke-status.md` documenting why the base-only probe smoke is currently blocked on local Python environment repair rather than repo code or Hugging Face cache.
- `examples/sample_eval_results.jsonl` as a clearly synthetic eval fixture for validating summary and plot tooling before Vikas's real eval JSONL lands.

## [v0.1.9] — 2026-04-29 — backlog-readiness-scaffold

### Added
- `BACKLOG.md` as the concrete execution queue for current, blocked, tabled, ready-when-inputs-land, and done work before the project sync.
- `docs/handoff-contracts.md` and `docs/alex-ready-runbook.md` to define checkpoint/eval JSONL handoffs and the exact commands Alex should run once teammate artifacts land.
- `scripts/validate_handoffs.py`, `scripts/summarize_eval_results.py`, and `scripts/plot_eval_results.py` so checkpoint/eval artifacts can be validated, summarized, and plotted without depending on unmerged env code.
- `scripts/test_readiness_tools.py` no-model smoke tests for the readiness scripts.

## [v0.1.8] — 2026-04-27 — optional-anthropic-generator

### Added
- Optional Anthropic API shell-game generator documentation in `README.md` and `docs/manual-shell-game-generation.md`, explicitly marking `dataset/generate.py` as a fallback/comparison path rather than the canonical data source for the current 100 honest + 100 deceptive local dataset.

### Changed
- `dataset/generate.py` now treats the Anthropic SDK as a runtime-only dependency, defaults to `data/anthropic_smoke`, bounds consecutive parse retries, and validates generated JSONL with `experiments/validate_shell_game_jsonl.py` by default after generation.
- The optional Anthropic generator now rejects invalid stages, negative requested counts, and malformed existing JSONL before generating more records; docs also call out the `--model` override for account-specific Anthropic model aliases.

## [v0.1.7] — 2026-04-27 — probe-scaffold

### Added
- `probes/` — Alex's research-lane scaffolding for the layer-migration plot (money shot).
  - `probes/extract.py` — `extract_activations(model_id, adapter_path, prompts, device)` pulls last-token residual-stream states at every transformer block (skips the embedding; layers 1..L) via `output_hidden_states=True`. CUDA/MPS/CPU device+dtype selection mirrors `experiments/sft_fix.py` (CUDA bf16, MPS fp32). Saves to `outputs/activations_{stage}.npz` with sidecar JSON metadata (`run_id`, `stage`, `prompts`, `layer_count`, `hidden_dim`, `n_prompts`).
  - `probes/train.py` — `train_probes(activations, labels)` fits a per-layer `sklearn` `LogisticRegression` (`class_weight="balanced"`, `liblinear` solver) with a 20% stratified holdout (`random_state=42`). Returns `{layer_idx: {auc, acc, coef_norm}}`. Serialized to `outputs/probe_results_{stage}.json`.
  - `probes/plot.py` — `plot_layer_auc(results_by_stage)` draws one line per stage (consistent colors: base/gray, control_sft/blue, honest_sft/green, control_corrupt/red, honest_corrupt/orange), chance line at 0.5, saved at `outputs/layer_migration.png` dpi=200.
  - `probes/run_all.py` — argparse CLI driver wiring extract → train → plot over a list of `stage:adapter_path` specs and a contrastive prompts JSONL.
  - `probes/test_probes.py` — synthetic-data smoke test (no model download). Gaussian signal planted near the middle layer; asserts peak AUC > 0.7 and peak-layer within ±5 of the expected location. Runs in <1s.
  - `probes/__init__.py` — lazy exports for `extract_activations`, `load_probe_examples`, `train_probes`, and `plot_layer_auc` so light imports do not require heavyweight ML dependencies.
- Probe loader support for both prompt+label JSONL and frozen shell-game SFT `messages` JSONL, including explicit `--trace-smoke` label-leakage warnings for pipeline-only validation.
- Activation archives now carry labels, record IDs, and per-record metadata alongside the residual-stream tensor so downstream plots can audit provenance.
- Probe CLI controls for device, Hugging Face token, and tokenizer max length; default adapter-path preflight; run-ID-scoped artifact names; and optional prompt sidecar storage.

### Decided
- **Layer convention:** skip embedding hidden state (index 0), keep blocks 1..L. Gemma-2-2b-it → 26 probe layers, hidden_dim 2304.
- **Probe recipe:** sklearn logistic regression, `class_weight="balanced"`, `liblinear` solver, 20% stratified holdout, `random_state=42`. Speed > elegance for the 5-day crunch.
- **Stage matrix:** default probe runs cover `base`, `control_sft`, `honest_sft`, `control_corrupt`, and `honest_corrupt` adapters.

## [v0.1.6] — 2026-04-27 — auto-approval-workflow

### Added
- GitHub Actions manual auto-approval workflow copied from `ai-coding-agents` so reviewed PRs can be approved through `gh workflow run`.

### Changed
- Project working conventions now state that GitHub PRs default to squash merge.

## [v0.1.5] — 2026-04-26 — execution-plan-flow

### Added
- Execution-plan flowchart in `README.md` showing Rithika, Vikas, Alex, and team-integration dependencies, concurrency, task owners, effort sizes, and key risks.
- `docs/execution-plan.md` companion notes covering the critical path, handoffs, and definition of done.

## [v0.1.4] — 2026-04-25 — shell-game-freeze-audit

### Added
- `experiments/prepare_shell_game_data.py` to freeze the validated local shell-game dataset, write SHA-256 manifest metadata, generate human-readable Markdown review files, and convert records into TRL-ready message-only SFT JSONL.

## [v0.1.3] — 2026-04-24 — manual-data-validation-note

### Validated
- First 100 honest + 100 deceptive shell-game examples were generated through the manual/basic workflow and validated locally; they were not generated through the optional OpenAI GPT-4o API smoke-test path.

## [v0.1.2] — 2026-04-24 — openai-shell-game-smoke

### Added
- `experiments/generate_shell_game_openai.py` for small GPT-4o Responses API shell-game generation batches with Structured Outputs, JSONL writing, validator integration, usage logging, and estimated GPT-4o token cost.

## [v0.1.1] — 2026-04-24 — manual-shell-game-data

### Added
- Manual paste-prompt shell-game data workflow in `docs/manual-shell-game-generation.md`, plus `experiments/validate_shell_game_jsonl.py` to validate JSONL syntax, message structure, scratchpad/dealer tags, and honest/deceptive position invariants before training.

## [v0.1.0] — 2026-04-24 — repo-bootstrap

### Project kickoff
- Repo initialized from Alex's personal class workspace. `PLAN.md`, `experiments/sft_fix.py`, and a v2 Colab notebook migrated over. AI motivation research PDFs and the project-notes markdown stay in the personal class repo as historical context.
- Team lanes confirmed: Rithika owns the training pipeline + checkpoints, Vikas owns the env + evaluation, Alex owns probing + analysis + research narrative. Swapped from Codex's initial suggestion so the "internal polygraph" novel contribution is owned by the lane closest to the research story.
- 5-day compressed schedule locked (Fri Apr 24 → Wed Apr 29 working deadline; May 5 presentation; May 12 final report). Table in `PLAN.md`.

### Added
- `README.md` — project overview, lanes, repo layout, `sft_fix.py` provenance + function, compute targets, references.
- `PLAN.md` — living 5-day plan with per-person per-day table, shared artifact JSONL contract, decision log.
- `experiments/sft_fix.py` — portable SFT pipeline (CUDA 4-bit/bf16, MPS fp32, CPU fallback). Device-aware dtype, `prepare_model_for_kbit_training` on both arms, messages-format training data, greedy eval, LoRA r=16/α=32 on q+k+v+o, `max_grad_norm=0.3`.
- `notebooks/sft_pipeline_v2_2026-04-24.ipynb` — Colab-runnable self-contained notebook mirroring `sft_fix.py`. For Rithika's iteration.
- `.gitignore` — Python/ML artifacts, large binaries (`*.pt`, `*.safetensors`, `*.pptx`), gitignored `data/outputs/checkpoints` contents with `.gitkeep` markers.

### Diagnosed (Rithika's v1 notebook)
Four bugs in `Big_Data_Analytics_Final_Project.ipynb` (the v1 that produced `"I I I I..."` gibberish with training loss 10.67):
1. LR `5e-6` — ~40× too low for LoRA on a 2B model.
2. Missing `prepare_model_for_kbit_training` before the control arm (called only before the honest arm).
3. `{"text": prompt+completion}` training format trains on user prompt tokens; loss 10.67 was partially this.
4. Aggressive sampling gen params (`do_sample=True, repetition_penalty=1.2, min_new_tokens=20`) amplified broken adapters into plausible-sounding gibberish, masking the training failure.

### Validated
- End-to-end SFT pipeline smoke-tested on M5 Max with `Qwen/Qwen2.5-1.5B-Instruct` as a stand-in for Gemma (at validation time the Gemma 2 license hadn't been accepted yet). Training loss converged cleanly 4.4 → 1.8 across 5 epochs, no NaN gradients — confirming the fixes work.
- Separately confirmed an earlier failure mode: bf16 + MPS with LR 2e-4 overflowed gradients on step 3 (`grad_norm: inf → nan → loss=0`). Resolution: fp32 on MPS, bf16 only on CUDA. This gates the `TRAIN_BF16` switch in the script.
- Twenty toy examples overfit both adapters into identical degenerate output on the smoke-test data. **This is a data issue, not a pipeline issue** — real training will use ~100 shell-game transcripts produced by Vikas's env.

### Decided
- **Compute:** M5 Max (local, fp32 MPS) + Colab Pro+ (CUDA, bf16 + 4-bit). Insomnia HPC skipped — overkill for a 2B model and not worth the access-setup cost given the 5-day window.
- **RL method:** SFT on deceptive traces (behavior cloning). DPO is the stretch target; PPO is out of scope for 3 weeks.
- **Eval envs:** Shell-game + minimal Python-scripting transfer env. Python transfer is a single test case (not a suite) to fit the schedule.

### References migrated
- Reference repo format adopted from this team's midterm project: https://github.com/rithika-d/Big_Data_Analytics_Midterm_Project
- Structural patterns borrowed from Alex's HPML COMS-E6998 project (`~/coding/Classes/COMS-E6998/Final_Project/`).
