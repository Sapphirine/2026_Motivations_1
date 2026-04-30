# Changelog

All notable changes and activity for **The Slippery Slope** final project. Semantic versioning (`vX.Y.Z — YYYY-MM-DD — <slug>`); every commit bumps at least the patch number. Doubles as an activity log — meetings, key decisions, and experimental results alongside code changes.

## [Unreleased]

Entries accumulate here until the next version bump.

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
- `BACKLOG.md` as the concrete execution queue for current, blocked, tabled, ready-when-inputs-land, and done work before the Wednesday sync.
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

## [v0.1.5] — 2026-04-26 — wednesday-call-flow

### Added
- Wednesday-call execution flowchart in `README.md` showing Rithika, Vikas, Alex, and team-integration dependencies, concurrency, task owners, effort sizes, and key risks.
- `docs/wednesday-call-execution-plan.md` companion notes covering the critical path, handoffs, and Wednesday definition of done.

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
