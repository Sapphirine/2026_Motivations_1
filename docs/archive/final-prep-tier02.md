# Final-Prep Tier 2 — Canonical Multi-Seed + Scaled SFT + Held-Out Family Experiment

Status: approved for implementation (v12 review complete, 2026-05-03) — scrub-gate canary fix + minor polish
Owner: Alex
Companion spec: [`final-prep-tier02_spec.md`](final-prep-tier02_spec.md)
Implementation branch: `codex-mle/tier02-plan-cleanup` branched from `mle/final-prep-t02`
Worktree: `.codex/worktrees/codex-mle-tier02-plan-cleanup`

## Origin

Tier 2 was identified in `~/coding/Classes/EECS-E6895/Final_Project/planning/tier-analysis-2026-05-03.md` (Tier 2 table, lines 89–99) as the post-May-5 paper-rigor scope. The paper deadline is 2026-05-12; Tier 2 work should finish by 2026-05-10 to leave 48 hours for writing.

Tier 2 is the project's **canonical public experiment**. Per the public-cleanup directive issued 2026-05-03, the final deck and report frame Tier 2 as the headline run, not as a "rescue" or "clean rerun" of an earlier Path A. Internal narrative about leakage and rescue is preserved privately under `~/coding/Classes/EECS-E6895/Final_Project/planning/`; it does not surface in grader-facing artifacts.

Seed artifacts that motivated Tier 2:

- `still-relevant-findings-2026-05-03.md` — internal review noting that single-seed corruption training underweights variance reporting, and that ~100-row SFT is small enough that data idiosyncrasies could dominate.
- `path_a_internal_analysis_2026-05-03.md` — post-rerun assessment showing the corruption asymmetry (control vs honest under corruption) is interesting but rests on a single training seed and a single SFT corpus version.
- Tier 1 evidence at `outputs/path_a_expanded_20260503_140104/` — current canonical baseline. `manifest.json` lists single-seed `control_clean_corrupt` and `honest_clean_corrupt` stages with adapter sha256s; `eval_expanded.reassembled.jsonl` is the deterministic-reassembly probe-input source; `lexical_baseline.json`, `probe_summary.md`, and `bootstrap_summary.md` are the per-cell evidence for behavior + probe + lexical canary. Tier 2 anchors comparisons against this exact path with a SHA ledger (M3).

Cross-agent review v1 (Codex, 2026-05-03 17:31) returned 1 Critical / 7 High / 4 Medium / 2 Low findings. v2 incorporates every Critical/High and reflects the public-cleanup directive in stage names, evidence paths, and report framing. Findings details and rebuttals live in §"Review Decisions" below.

Backlog lineage:

- `pm/backlog.md` (if present): tracked items under "planned probe upgrade" and "tier-2 multi-seed retraining" feed this plan. Tier 3 follow-ups such as activation steering and multi-task probe transfer are tracked outside this branch.
- This plan does not introduce new backlog items beyond Tier 2 scope.

Reference state of the world (post Tier 0/1 / PR #8):

- `experiments/train_clean_corruption.py` — parameterized for stages, parents, dataset; **lacks** `--seed`, `--stage-name`, `--overwrite` (Phase 0.5 adds these).
- `data/shell_game_v1/shell_game_{deceptive,honest}.sft.jsonl` — 100/100 frozen rows. **Does not** carry `prompt_family` metadata. v2 corpus must add it.
- `outputs/path_a_expanded_20260503_140104/` — Tier 1 expanded eval, post-PR9. Eval rows contain `prompt_family`, `prompt_variant`, `prompt_seed`, `prompt_id`, `true_position`, `claimed_position`, `is_deceptive`, `parser_error`.
- `scripts/eval_runner.py` v2 — sharded eval with per-cell `config_hash` over ordered `(stage, adapter_path, adapter_dir_sha256)` pairs. Cross-root resume is **not** supported (H4).
- `scripts/assemble_eval.py` — takes `--manifest`, optional `--shard-dir`, optional `--output`. **No** `--strict` flag (H5 fix).
- `scripts/summarize_eval_results.py` — emits Markdown by stage/benchmark; **no** `--plot` flag. Plotting lives in `scripts/plot_eval_results.py` (H5 fix).
- `scripts/build_probe_inputs_from_eval.py` — emits per `(stage, condition)` JSONL with `label` (int 0/1) and `record_id` per row. No family filter; Phase 4 adds an out-of-band split.
- `probes/run_all.py` — `--stages stage:path` repeated arguments (L1). Internal CV; **does not** support fit-on-A / eval-on-B transfer mode (H6 — Tier 2 adds `scripts/probe_transfer.py`).
- `probes/train.py` — returns dict keyed by layer index; balanced-accuracy + bootstrap-CI patches landed in PR #8.
- `scripts/bootstrap_ci.py` — class-stratified bootstrap with single-class-resample guard.
- `scripts/lexical_baseline.py` — TF-IDF + LR canary; consumes `probe_inputs/*.jsonl` rows directly (H7 fix specifies inputs).
- `envs/shell_game.py` — `_PROMPT_VARIANTS` ≥ 40 templates, `prompt_family` metadata via `prompt_variant_family(...)`.

## Stage matrix (canonical naming)

```
base
control_sft
honest_sft
control_corrupt_s42
control_corrupt_s1337
control_corrupt_s2024
honest_corrupt_s42
honest_corrupt_s1337
honest_corrupt_s2024
```

The Tier 1 stages `control_clean_corrupt` / `honest_clean_corrupt` are renamed to `control_corrupt` / `honest_corrupt` in all Tier 2 grader-facing artifacts. Internal references to the older naming remain in PR #8 evidence under `outputs/path_a_expanded_20260503_140104/` and `deliverables/evidence/path_a_clean_20260503/`; those paths are not extended in Tier 2.

## Scope — what's in, what's out

In:

1. **Public cleanup** — scrub rescue/clean-run framing and narrative leak-history phrases from `README.md`, `CHANGELOG.md`, `docs/final-presentation-draft.md`, `docs/final-report-skeleton.md`, `docs/deck-skeleton.md`, `docs/local-probe-smoke-status.md`. Preserve standard ML uses such as "label leakage" when they describe a technical risk. Move the historical narrative to `~/coding/Classes/EECS-E6895/Final_Project/planning/`.
2. **Script preflight** — extend `experiments/train_clean_corruption.py` with `--seed`, `--stage-name`, `--overwrite`, `--dataset-sha256` recording.
3. **Improved corpus** — `$ARTIFACT_ROOT/data/shell_game_v2/`, ~500 deceptive + ~500 honest rows. Generation increases prompt-family diversity by emitting `prompt_family` metadata via the `_PROMPT_VARIANTS` registry rather than copying templates 5×. **All-family build target ≥ 7 distinct families × ≥ 50 rows each** (v2 M2: post-holdout corpus must still have ≥ 6 families). ≥ 12 unique `(template_id, persona, position, truth)` combinations per family. Tie-breaking for "dominant training-data family" in P1.5.0: among families tied for largest count, exclude only the candidate with highest `predicted_per_cell`; if still tied, lexicographic order on family name (deterministic).
4. **Held-out prompt family** — declare one family at v2 build time; train on in-family rows only; eval on both in-family and held-out families with explicit row-count gate (H2).
5. **Multi-seed retraining** — 3 training seeds × 2 corruption stages = 6 new adapters under `checkpoints/tier2_corruption/`. **Both** stages train on `data/shell_game_v2/shell_game_deceptive.sft.jsonl` (C1 fix). Parent adapter is what differentiates control vs honest.
6. **Full canonical eval** — fresh 9-stage × 2-condition × 150-round sharded run under `deliverables/evidence/canonical_tier2_<DATE>/eval/`. **No cross-root reuse** of Tier 1 shards (H4).
7. **Per-cell probes** — for each `(stage, condition)` cell. Plus `scripts/probe_transfer.py` (new) for true in-family→held-out generalization.
8. **Per-cell bootstrap CIs and lexical canary** — same Tier 1 contract; lexical AUC reported as **disclosure**, not a hard blocker (H7).
9. **Seed-aggregated layer-migration plot** with min/max bands; **ablation table** rows for seed/corpus/family axes.
10. **Doc updates** — `docs/final-presentation-draft.md` and report draft cite Tier 2 as the canonical experiment. Optional post-presentation deck refresh.
11. **Acceptance gate** — public-surface grep for blocked terms.
12. **CHANGELOG `[Unreleased]` entries + version bump**.

Out:

- DPO/PPO retraining (Tier 4).
- Activation steering, causal mediation, multi-task probe transfer (Tier 3).
- Larger-model swaps (Tier 3/4).
- Re-running Tier 1 base + parent SFT stages (locked at PR #8).
- Editing PR #8 evidence directories.
- Mid-Tier-2 deck swaps into the May 5 PPTX (locked 2026-05-04 18:00).

## Phase 0 — Preconditions, public cleanup, script preflight

Wall budget: ≤ 4 hours.

### File-by-file checklist

- [x] **P0.1 Tier 1 baseline ledger** — write `$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_baselines.md` (v9 M1 — strict schema since this file is in the scrub scope):
  - **Schema** — Markdown table with these columns only: `Display label | Frozen prior path | sha256`. The `Display label` column uses canonical names (`Tier-1 expanded eval manifest`, `Tier-1 reassembled eval JSONL`, `Tier-1 probe summary`, `Tier-1 lexical canary`, `Tier-1 bootstrap summary`). The `Frozen prior path` column carries the raw filesystem paths (`outputs/path_a_expanded_20260503_140104/...`); these path strings are explicitly OK because the scrub regex's `path_a_clean` term matches only `path_a_clean`, not `path_a_expanded`. The ledger MUST NOT copy/paste manifest stage names, legacy evidence directory names like `path_a_clean_20260503/`, or any rescue-narrative prose. SHA values only.
  - **Files to ledger:**
    - `$ARTIFACT_ROOT/outputs/path_a_expanded_20260503_140104/manifest.json`
    - `$ARTIFACT_ROOT/outputs/path_a_expanded_20260503_140104/eval_expanded.reassembled.jsonl`
    - `$ARTIFACT_ROOT/outputs/path_a_expanded_20260503_140104/probe_summary.md`
    - `$ARTIFACT_ROOT/outputs/path_a_expanded_20260503_140104/lexical_baseline.json`
    - `$ARTIFACT_ROOT/outputs/path_a_expanded_20260503_140104/bootstrap_summary.md` (if present)
  - **Framing line at top of ledger:** "Frozen Tier-1 prior evidence retained for SHA-pinned comparison only. Not a public-story reference; canonical Tier 2 evidence supersedes it." No mention of leak/rescue/clean rerun in the framing.
  - **Acceptance:** file exists; all listed sums computed against `$ARTIFACT_ROOT` paths; `grep -inE "$CANONICAL_SCRUB_REGEX" $WORKTREE_ROOT/deliverables/evidence/canonical_tier2_baselines.md` returns no matches (path strings under `outputs/path_a_expanded_*` do not trip the regex).
- [x] **P0.2 Worktree ground state** — `git status --porcelain --branch` shows `codex-mle/tier02-plan-cleanup` clean and not behind its base. Acceptance: clean output, no untracked critical paths.
  - **Implementation result:** branch remained on `codex-mle/tier02-plan-cleanup`; pre-final status showed only expected docs/code edits and small mirrored Markdown summaries, with no raw artifact paths. Final clean status is verified after the closing commit.
- [x] **P0.3 Disk + wall budgets**
  - **Task:** `df -h /Users/wax/coding/The_Slippery_Slope` returns ≥ 5 GB free. Schedule contiguous 24–36 hr compute window 2026-05-06..09.
  - **Acceptance:** `df` ≥ 5 GB free; calendar slot reserved.
  - **Implementation result:** disk check showed 289 GiB free on `/System/Volumes/Data`; the resumed run completed inside this session, so no additional 24–36 hour slot was needed.
- [x] **P0.4 Env preflight**
  - **Task:** `PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python; "$PY" -c 'import torch, transformers, peft, trl, sklearn, datasets'`. `HF_TOKEN` env var set.
  - **Acceptance:** import line exits 0, prints nothing; `[ -n "$HF_TOKEN" ]` true.
- [x] **P0.4.1 Two-root anchors** (v3 H1, v4 H1)
  - **Task:** export both:
    - `ARTIFACT_ROOT=/Users/wax/coding/The_Slippery_Slope` — for **gitignored compute artifacts** that already live in the root tree: parent SFT adapters, Tier 1 baseline outputs at `outputs/path_a_expanded_20260503_140104/`, all Tier 2 checkpoints at `checkpoints/tier2_corruption/`, all Tier 2 generated data at `data/shell_game_v2/`. These never enter the worktree.
    - `WORKTREE_ROOT=/Users/wax/coding/The_Slippery_Slope/.codex/worktrees/codex-mle-tier02-plan-cleanup` — for **branch-tracked docs and tracked deliverables**: plan/spec at `docs/plans/`, evidence Markdown summaries at `deliverables/evidence/canonical_tier2_<DATE>/` (the directory itself is gitignored except for the small Markdown summaries we explicitly track per `.gitignore` patterns), CHANGELOG, README, etc.
  - **Why two roots:** all heavy compute artifacts (adapters, raw eval JSONL, activations) are gitignored anyway, so writing them under `$ARTIFACT_ROOT` keeps the worktree small and prevents the "wrote to worktree, eval reads from root" mismatch. Branch-tracked artifacts live under `$WORKTREE_ROOT` so commits land on `codex-mle/tier02-plan-cleanup`. Evidence directories use `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/` for raw JSONL/.npz files; the **selected** Markdown summary files (e.g., `probe_summary.md`, `family_comparison.md`, `behavior_summary.md`, `lexical_summary.md`, plot PNGs we want to commit) are copied/symlinked into `$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_<DATE>/` for tracking.
  - **Acceptance:** `[ -d "$ARTIFACT_ROOT/checkpoints/gemma_control_sft/final_adapter" ] && [ -d "$ARTIFACT_ROOT/checkpoints/gemma_honest_sft/final_adapter" ] && [ -d "$ARTIFACT_ROOT/outputs/path_a_expanded_20260503_140104" ] && [ -d "$WORKTREE_ROOT/docs/plans" ]` all true.
- [x] **P0.5 Strict public + canonical-surface scrub** (v8 user directive — strict `_clean` removal)
  - **Task:** rewrite passages that frame the project as "rescue / leak discovery / clean rerun" into the canonical-experiment framing. Preserve standard technical terms such as "label leakage" and "leakage-aware" when they describe train/test or trace-label risks. Replace stage names `control_clean_corrupt` → `control_corrupt`, `honest_clean_corrupt` → `honest_corrupt` in **all** grader-facing and canonical Tier 2 prose. Move removed historical narrative chunks to `~/coding/Classes/EECS-E6895/Final_Project/planning/preserved-rescue-narrative-<DATE>.md` (personal class repo, never shipped to graders).
  - **In-scope files (canonical surfaces — must be clean of all blocked terms):**
    - `README.md`, `CHANGELOG.md`
    - `docs/final-presentation-draft.md`, `docs/final-report-skeleton.md`, `docs/deck-skeleton.md`, `docs/local-probe-smoke-status.md`
    - All branch-tracked Markdown and PNG metadata under `$WORKTREE_ROOT/data/shell_game_v2/` (`MANIFEST.md`, `holdout_family.md`, `review.md`, `*.review.md`)
    - All branch-tracked Markdown and PNG mirrors under `$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_<DATE>/` (`behavior_summary.md`, `behavior_deception_rate.png`, `seed_aggregated_summary.md`, `layer_migration_seedbands.png`, `family_comparison.md`, `ablation_table.md`, `lexical_summary.md`)
    - `$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_baselines.md` (the SHA ledger from P0.1)
    - Optional post-presentation deck `deliverables/slippery-slope-results-paper-<DATE>.pptx` (text extracted via `unzip -p ... 'ppt/slides/*.xml'`).
  - **CANONICAL_SCRUB_REGEX (defined once here; referenced by P6.4, P6.5.2, spec § 14, Review Decisions):** `path_a_clean|clean[- ]data|clean rerun|rescue|leakage-driven|leak-driven|leak discovery` — case-insensitive. The pattern targets narrative leak-history phrasing, rescue/clean-run framing, and the path slug. It intentionally does **not** ban standard technical uses such as "label leakage," required script filenames such as `experiments/train_clean_corruption.py`, or historical internal stage-key notes.
  - **Implementation exception (NOT in scope of the scrub gate):**
    - `experiments/train_clean_corruption.py` (filename and module — renaming churns imports for no grader-facing benefit; the script's `STAGE_DEFAULTS` keys `control_clean_corrupt` and `honest_clean_corrupt` remain as **internal parent-adapter selection keys** invoked via `--stages control_clean_corrupt --stage-name control_corrupt_s$seed`).
    - Code comments and docstrings in `scripts/` and `probes/` referencing the internal stage keys.
    - PR #8 evidence directories (`outputs/path_a_expanded_20260503_140104/`, `deliverables/evidence/path_a_clean_20260503/`) — frozen historical artifacts; referenced in Tier 2 only via the **SHA ledger** in P0.1, never linked from grader-facing prose.
    - `docs/plans/final-prep-tier02*.md` (this plan/spec — internal planning, not grader-facing; references the internal `STAGE_DEFAULTS` key when documenting commands).
    - `~/coding/Classes/EECS-E6895/Final_Project/planning/preserved-rescue-narrative-<DATE>.md` (personal class repo; outside team-repo scope).
  - **Acceptance** (v9 H1 + v10 H1 — robust against missing future paths and tracked/untracked drift):

    The gate is a wrapper script that builds the target list dynamically (skipping nonexistent files/dirs at Phase 0 entry) and treats grep's exit code 1 (no matches) as success:

    ```bash
    CANONICAL_SCRUB_REGEX='path_a_clean|clean[- ]data|clean rerun|rescue|leakage-driven|leak-driven|leak discovery'

    scrub_gate() {
      # Allowlist-style target list. Excluded paths (docs/plans/, experiments/,
      # .codex/, .claude/) are simply absent from the list — no negative-glob
      # mechanism needed.
      local targets=()
      local f
      for f in \
        $WORKTREE_ROOT/README.md \
        $WORKTREE_ROOT/CHANGELOG.md \
        $WORKTREE_ROOT/docs/final-presentation-draft.md \
        $WORKTREE_ROOT/docs/final-report-skeleton.md \
        $WORKTREE_ROOT/docs/deck-skeleton.md \
        $WORKTREE_ROOT/docs/local-probe-smoke-status.md \
        $WORKTREE_ROOT/data/shell_game_v2/MANIFEST.md \
        $WORKTREE_ROOT/data/shell_game_v2/holdout_family.md \
        $WORKTREE_ROOT/data/shell_game_v2/review.md \
        $WORKTREE_ROOT/deliverables/evidence/canonical_tier2_baselines.md
      do
        [ -e "$f" ] && targets+=("$f")
      done
      # *.review.md glob (zero or more files)
      shopt -s nullglob
      for f in $WORKTREE_ROOT/data/shell_game_v2/*.review.md; do
        targets+=("$f")
      done
      # canonical-tier2 evidence dir (may not exist at Phase 0)
      [ -d "$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_<DATE>" ] && \
        targets+=("$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_<DATE>")
      shopt -u nullglob
      [ "${#targets[@]}" -eq 0 ] && { echo "no targets exist yet"; return 0; }
      # exit 0 (clean) when grep finds nothing; exit 1 if blocked term found
      if grep -inEr --include='*.md' --include='*.png' --include='*.txt' --include='*.tmp' \
           "$CANONICAL_SCRUB_REGEX" "${targets[@]}"; then
        return 1   # blocked term found
      fi
      return 0     # clean
    }
    ```

    Run as: `scrub_gate || { echo "Tier 2 scrub gate failed"; exit 1; }`.

    **Canary verification** (proves the gate has teeth, not just no targets):
    ```bash
    mkdir -p $WORKTREE_ROOT/data/shell_game_v2
    # Use the *.review.md naming so the canary file is picked up by the
    # nullglob expansion of $WORKTREE_ROOT/data/shell_game_v2/*.review.md
    # in scrub_gate's target list. A bare _gate_canary.md would NOT be
    # in the target list because the list is allowlist-style.
    echo 'rescue' > $WORKTREE_ROOT/data/shell_game_v2/_gate_canary.review.md
    scrub_gate && echo "BUG: canary not detected" && exit 1
    rm $WORKTREE_ROOT/data/shell_game_v2/_gate_canary.review.md
    scrub_gate || { echo "still dirty after canary removal"; exit 1; }
    ```
- [x] **P0.6 Script preflight upgrades to `experiments/train_clean_corruption.py`** (v2 H3, v2 M4, v3 M5)
  - **Task:** add the **three new CLI flags**: `--seed <int>` (calls `transformers.set_seed`, `torch.manual_seed`, threads through `SFTConfig.seed=`, sets `Dataset.shuffle(seed=...)` if shuffling), `--stage-name <str>` (overrides the directory leaf so each seed writes to its final path, e.g., `--stage-name control_corrupt_s42`), and `--overwrite` (default False; if False and `<output_root>/<stage_name>/final_adapter` exists, exit 1). **Additionally** compute `dataset_sha256` internally (no CLI flag) and persist `seed`, `stage_name`, `final_adapter_path`, `parent_adapter_sha256`, `dataset_sha256`, `train_loss_final` to `run_metadata.jsonl` after final save.
  - **Acceptance:** `"$PY" experiments/train_clean_corruption.py --help` lists the **three** new flags (`--seed`, `--stage-name`, `--overwrite`). `run_metadata.jsonl` includes `dataset_sha256` (computed internally, not a flag). Re-running with the same seed and `--overwrite` produces a directory whose final train loss matches the previous run within ±0.02 (soft tolerance per v2 M4; not a bitwise check). Re-running without `--overwrite` against an existing path exits 1 with a clear message.
- [x] **P0.7 Probe transfer-mode tool + activation cache** (v2 H5, v2 H7, v2 L1, v3 C1, v3 H4)
  - **Task:** add `scripts/probe_transfer.py` (new, ~200 lines) AND `scripts/extract_probe_activations.py` (new, ~180 lines).
    - **`extract_probe_activations.py`** CLI: `--prompts <jsonl>`, `--stages stage:adapter_or_none`, `--stage-name <str>`, `--condition <str>`, `--family-split <"infamily"|"holdout">`, `--out <activations.npz>`, `--max-length`, `--device`, `--overwrite`. The CLI explicitly carries `--stage-name`, `--condition`, `--family-split` so the sidecar can record the cell identity (v4 H3). Reads the prompts JSONL **once** to anchor row identity, then writes a self-contained `.npz` containing:
      - `activations`: shape `(n_rows, n_layers, hidden_dim)` (or per-layer arrays if memory dictates)
      - `labels`: shape `(n_rows,)` int array, copied from each row's `label` field in the JSONL (the existing convention emitted by `scripts/build_probe_inputs_from_eval.py` and consumed by `probes/run_all.py`; the extractor accepts `behavior_label` as an alias for backward compatibility but defaults to `label`)
      - `record_ids`: shape `(n_rows,)` string array, copied from each row's `record_id` in stable order
      - **Sidecar JSON** (`<.npz>.json`) with `schema_version: 1` plus all of: `stage`, `condition`, `family_split`, `adapter_kind` (`"base"` when `--stages base:none`, else `"lora"`), `model_id`, `adapter_dir_sha256` (`null` when `adapter_kind == "base"`, else the eval_runner.sha256_tree of the adapter dir), `layer_count`, `hidden_dim`, `record_count`, `prompt_jsonl_sha256` (sha256 of the source JSONL bytes), `labels_sha256` (sha256 of the labels array bytes), `record_ids_sha256` (sha256 of `b"\n".join(record_ids.astype(bytes))`), `prompt_render_sha256` (sha256 of `envs/shell_game.py` source).
      - **Idempotence**: if `.npz` and sidecar exist and sidecar hashes still match the current source JSONL, model id, and adapter, skip extraction unless `--overwrite`.
    - **`probe_transfer.py`** CLI: `--train-activations <npz>`, `--eval-activations <npz>`, `--out-dir <dir>`, `--max-layers <int>` (default 0 = all 26), `--seed <int>` (default 42). **Reads labels and record_ids from the .npz directly** (closes C1 integrity gap). **Cache-pairing validation** (v4 H3): asserts train and eval sidecars share `stage`, `condition`, `adapter_kind`, `model_id`, `adapter_dir_sha256` (both `null` is OK when `adapter_kind == "base"`), `layer_count`, `hidden_dim`, `prompt_render_sha256`; asserts `family_split` differs (`infamily` for train, `holdout` for eval). Aborts on any mismatch. Fits one logistic-regression probe per layer on the train activations, evaluates on the eval activations (no CV mixing, no fallback). Writes `probe_results_transfer.json` matching the **existing probe schema 2**: `{schema_version: 2, status, cell, n_train, n_eval, per_layer: {<layer_index>: {y_test, proba_test, pred_test, auc, balanced_accuracy, n_test}}}`. For degenerate cells (`min(pos, neg) < 5` on either side): `status: "degenerate"`, no `per_layer` payload, `auc: null` and `balanced_accuracy: null` at top level. **Never** falls back to within-train CV.
  - **Acceptance:** smoke run uses the actual P4.2 output shape: invoke `build_probe_inputs_from_eval.py` on a 40-row mini-eval JSONL, then run `extract_probe_activations.py` against the resulting `<stage>__<condition>.jsonl` (which has `label` and `record_id` per row), then run extraction a second time (no-op). Run probe_transfer with `--max-layers 1`. Output JSON has `schema_version: 2`, `cell`, `n_train`, `n_eval`, `per_layer: {0: {y_test, proba_test, pred_test, auc, balanced_accuracy, n_test}}`. Tampering with the labels in one .npz (e.g., flipping bits) and re-running probe_transfer must abort with a clear message that the cached label hash no longer matches.
- [x] **P0.5.1 Canonical-name plot/legend update — existing plotters** (v8 user directive; v9 H3 — split per script lifecycle):
  - **Task:** update the **existing** plot-generation scripts so canonical Tier 2 stage names map cleanly:
    - `probes/plot.py` — add color/legend entries for `control_corrupt`, `honest_corrupt`, and the seed-suffixed forms `control_corrupt_s42`, `control_corrupt_s1337`, `control_corrupt_s2024`, `honest_corrupt_s42`, `honest_corrupt_s1337`, `honest_corrupt_s2024`. Pre-existing legacy `control_clean_corrupt` / `honest_clean_corrupt` entries may stay as backward-compat for PR #8 rerenders but must be flagged with a `# legacy-PR8-rerender-only` comment so they are not silently picked up during Tier 2 rendering.
    - `scripts/plot_eval_results.py` — same canonical color/legend mapping for the Tier 2 behavior plot (`behavior_deception_rate.png`).
  - **Acceptance:** `grep -nE 'control_corrupt|honest_corrupt' probes/plot.py scripts/plot_eval_results.py` shows the new canonical entries; `grep -nE '_clean_corrupt' probes/plot.py scripts/plot_eval_results.py` shows only entries clearly tagged `# legacy-PR8-rerender-only`. The new `scripts/plot_layer_migration_seeds.py` from P5.1 has its own canonical-name check in its acceptance — not gated here.
- [x] **P0.8 Internal-doc note** (replaces v2's plan-grep gate, per H3 review)
  - **Note:** Tier 2 plan + spec docs (`docs/plans/final-prep-tier02*.md`) are NOT grader-facing — they live under `docs/plans/` and are intentionally excluded from the public scrub gate. The plan must use the internal parent-key strings `control_clean_corrupt` and `honest_clean_corrupt` in P2.1/P2.2 commands because those are real `STAGE_DEFAULTS` keys in `experiments/train_clean_corruption.py`. This is by design; the `--stage-name` flag controls public output naming.
  - **Acceptance:** none. This is documentation, not a check.

### Phase 0 acceptance gates

- All P0.1–P0.8 boxes ticked.
- Script preflight committed to `codex-mle/tier02-plan-cleanup` (one commit).
- Public surface scrub committed (one commit).
- `scripts/probe_transfer.py` smoke-tested.

## Phase 1 — Improved SFT corpus (`data/shell_game_v2/`)

Goal: build a 500 deceptive + 500 honest SFT corpus that **adds** prompt-family diversity (not just row count), freeze it under `data/shell_game_v2/`, and emit `prompt_family` metadata in the SFT rows so the held-out family selection has something real to read.

### File-by-file checklist

- [x] **P1.0** — `experiments/scale_shell_game_data.py` (new, ~250 lines):
  - **Task:** templated-regen script. CLI: `--source $ARTIFACT_ROOT/data/shell_game_v1/shell_game_<stage>.sft.jsonl`, `--target-rows 500`, `--seed <int>`, `--out-dir $ARTIFACT_ROOT/data/shell_game_v2`. Mechanism: enumerate `(template_id, persona, position, truth, eval_condition)` tuples drawn from `envs.shell_game._PROMPT_VARIANTS` (≥ 40) × persona registry × position {0,1,2} × truth {True, False}; reject duplicate combinations; write each row with `prompt_family` (from `prompt_variant_family(...)`), `prompt_variant`, `persona`, `position`, `truth`, `messages`, `prompt_id`, `record_id`. **All-family build target ≥ 7 distinct families × ≥ 50 rows each** (v2 M2: post-holdout corpus must still have ≥ 6 families).
  - **Acceptance:** `wc -l $ARTIFACT_ROOT/data/shell_game_v2/shell_game_deceptive.sft.jsonl` returns 500; `wc -l $ARTIFACT_ROOT/data/shell_game_v2/shell_game_honest.sft.jsonl` returns 500; `"$PY" -c "import json; from collections import Counter; rows=[json.loads(l) for l in open('$ARTIFACT_ROOT/data/shell_game_v2/shell_game_deceptive.sft.jsonl')]; c=Counter(r['prompt_family'] for r in rows); print(c); assert len(c) >= 7 and min(c.values()) >= 50, c"` passes.
- [x] **P1.1** — Determinism + manifest:
  - **Task:** all randomness keyed on `--seed`. `$ARTIFACT_ROOT/data/shell_game_v2/MANIFEST.md` lists corpus seed, source, target rows, per-family counts, sha256 of each output JSONL, `schema_version: 1` (integer; v2 M4 fix).
  - **Acceptance:** running with same `--seed` twice → byte-identical outputs (`sha256sum` matches). MANIFEST contains all listed fields.
- [x] **P1.2** — Validation:
  - **Task:** `"$PY" experiments/validate_shell_game_jsonl.py $ARTIFACT_ROOT/data/shell_game_v2/shell_game_<stage>.sft.jsonl` for both stages.
  - **Acceptance:** validator exits 0 on both.
- [x] **P1.3** — Two-tree gitignore updates (v6 H1 — branch-tracked rules vs root-runtime exclude):
  - **Task A — branch-tracked rules in `$WORKTREE_ROOT/.gitignore`** (this is what gets committed onto `codex-mle/tier02-plan-cleanup` and shipped in the PR):
    ```
    # add (alongside existing `!data/shell_game_v1/...` block in $WORKTREE_ROOT/.gitignore):
    !data/shell_game_v2/
    !data/shell_game_v2/MANIFEST.md
    !data/shell_game_v2/*.review.md
    !data/shell_game_v2/review.md
    !data/shell_game_v2/holdout_family.md
    data/shell_game_v2/*.jsonl

    # plus, for canonical evidence — track only the Markdown/PNG summaries that get mirrored under $WORKTREE_ROOT:
    !deliverables/evidence/canonical_tier2_*/
    !deliverables/evidence/canonical_tier2_*/eval/
    !deliverables/evidence/canonical_tier2_*/eval/behavior_summary.md
    !deliverables/evidence/canonical_tier2_*/eval/behavior_deception_rate.png
    !deliverables/evidence/canonical_tier2_*/probes/
    !deliverables/evidence/canonical_tier2_*/probes/seed_aggregated_summary.md
    !deliverables/evidence/canonical_tier2_*/probes/layer_migration_seedbands.png
    !deliverables/evidence/canonical_tier2_*/probes/lexical_summary.md
    !deliverables/evidence/canonical_tier2_*/probes/family_comparison.md
    !deliverables/evidence/canonical_tier2_*/probes/ablation_table.md
    deliverables/evidence/canonical_tier2_*/eval/shell_eval.jsonl
    deliverables/evidence/canonical_tier2_*/eval/shards/
    deliverables/evidence/canonical_tier2_*/eval/manifest.json
    deliverables/evidence/canonical_tier2_*/probes/activations/
    deliverables/evidence/canonical_tier2_*/probes/within_subset_*/
    deliverables/evidence/canonical_tier2_*/probes/transfer/
    deliverables/evidence/canonical_tier2_*/probes/probe_inputs_*/
    deliverables/evidence/canonical_tier2_*/probes/lexical_*/
    deliverables/evidence/canonical_tier2_*/probes/*.json
    ```
    (The trailing `*.json` rule covers root-level probe JSON like `seed_aggregated.json` so a stray copy under `$WORKTREE_ROOT` will not silently land on the branch — only the `*_summary.md` summaries and PNGs are tracked.)
  - **Task B — root-runtime exclude in `$ARTIFACT_ROOT/.git/info/exclude`** (so the root checkout's `git status` does not get noisy with hundreds of untracked heavy artifacts; this file is local to the root tree, not committed):
    ```
    # append:
    /data/shell_game_v2/
    /checkpoints/tier2_corruption/
    /deliverables/evidence/canonical_tier2_*/
    ```
    The root tree never tracks Tier 2 artifacts; this just keeps `git status` quiet there.
  - **Acceptance:**
    - `git -C $WORKTREE_ROOT check-ignore -v data/shell_game_v2/shell_game_deceptive.sft.jsonl` returns the path (ignored).
    - `git -C $WORKTREE_ROOT check-ignore -v data/shell_game_v2/MANIFEST.md`, `.../review.md`, `.../holdout_family.md` all return nothing (tracked).
    - `git -C $WORKTREE_ROOT check-ignore -v deliverables/evidence/canonical_tier2_<DATE>/eval/behavior_summary.md` returns nothing (tracked).
    - `git -C $WORKTREE_ROOT check-ignore -v deliverables/evidence/canonical_tier2_<DATE>/eval/shell_eval.jsonl` returns the path (ignored).
    - `git -C $ARTIFACT_ROOT check-ignore -v data/shell_game_v2/` returns the path via `.git/info/exclude` (root-tree status quiet).
    - `git -C $ARTIFACT_ROOT check-ignore -v checkpoints/tier2_corruption/` returns the path (heavy adapter dir excluded from root-tree status).
    - `git -C $ARTIFACT_ROOT check-ignore -v deliverables/evidence/canonical_tier2_<DATE>/eval/shell_eval.jsonl` returns the path (heavy raw eval JSONL excluded).
- [x] **P1.4 Metadata mirror to WORKTREE_ROOT** (v4 H1 — bridge artifact tree to branch):
  - **Task:** the v2 corpus generation lives at `$ARTIFACT_ROOT/data/shell_game_v2/` (gitignored heavy JSONL stays there). Mirror the **tracked** metadata files into the worktree so `git commit` lands them on `codex-mle/tier02-plan-cleanup`:
    ```
    mkdir -p $WORKTREE_ROOT/data/shell_game_v2
    cp $ARTIFACT_ROOT/data/shell_game_v2/MANIFEST.md $WORKTREE_ROOT/data/shell_game_v2/
    cp $ARTIFACT_ROOT/data/shell_game_v2/holdout_family.md $WORKTREE_ROOT/data/shell_game_v2/ 2>/dev/null || true
    cp $ARTIFACT_ROOT/data/shell_game_v2/review.md $WORKTREE_ROOT/data/shell_game_v2/ 2>/dev/null || true
    cp $ARTIFACT_ROOT/data/shell_game_v2/*.review.md $WORKTREE_ROOT/data/shell_game_v2/ 2>/dev/null || true
    ```
    Per the gitignore rules in P1.3 (mirrored at the repo level, so the worktree inherits them), `*.jsonl` stays ignored under `$WORKTREE_ROOT/data/shell_game_v2/` even if it gets accidentally copied — only the tracked Markdown files end up on the branch.
  - **Acceptance:** `git -C $WORKTREE_ROOT status --porcelain data/shell_game_v2/` lists `MANIFEST.md`, `holdout_family.md`, `review.md` (if present), and `*.review.md` (if present) as new files, none of them ignored.

### Phase 1 acceptance gates

- 500/500 deterministic rows.
- ≥ 6 families × ≥ 50 rows each, with `prompt_family` field present in every row.
- MANIFEST committed; raw JSONL ignored.

## Phase 1.5 — Held-out family declaration (post-build)

Goal: pick the held-out prompt family **after** P1.0 has emitted v2 metadata, with an N-validity gate that anticipates Phase 4 row counts (H1, H2).

### File-by-file checklist

- [x] **P1.5.0** — Family inventory + exact predicted count (v2 H2):
  - **Task:** inspect `$ARTIFACT_ROOT/data/shell_game_v2/MANIFEST.md` per-family counts. For each candidate family, compute the exact predicted **per-cell** (not per-stage-pair) row count by simulating the eval seed loop:
    ```python
    from envs.shell_game import _PROMPT_VARIANTS, prompt_variant_family
    V = len(_PROMPT_VARIANTS)
    def predicted_per_cell(family, rounds, seed0=0):
        return sum(
          1 for s in range(seed0, seed0 + rounds)
          if prompt_variant_family(_PROMPT_VARIANTS[s % V], s % V) == family
        )
    ```
    The result is per `(stage, condition)` cell because eval_runner cycles the same seed range for each cell. Family with the highest `predicted_per_cell` that is **not** the dominant training-data family is the candidate.
  - **Acceptance:** decision recorded in `$ARTIFACT_ROOT/data/shell_game_v2/holdout_family.md` with: candidate family name, total v2 training-row count, exact predicted Phase 4 rows per `(stage, condition)` cell at the planned `--rounds`, the simulation snippet output, and the rationale.
- [x] **P1.5.1** — Hard N gate with parser-error safety margin (v2 H2):
  - **Task:** require `predicted_per_cell ≥ ceil(10 × 1.3) = 13` for every cell at the planned `--rounds` (the 1.3× margin anticipates parser-error exclusion in `build_probe_inputs_from_eval.py`, which has historically dropped 5–25% of rows on this model). If the best candidate predicts < 13 at `--rounds 100`, increase Phase 3 `--rounds` to the smallest multiple of 50 that satisfies the margin. Update `$ARTIFACT_ROOT/data/shell_game_v2/holdout_family.md` with the chosen `--rounds`.
  - **Acceptance:** chosen family + chosen rounds → exact predicted per-cell ≥ 13. The chosen `--rounds` propagates into Phase 3 commands.
  - **Implementation result:** holdout family `baseline`; full eval `--rounds 150` (15 predicted held-out rows per `(stage, condition)` cell).
- [x] **P1.5.2** — Rebuild v2 with holdout flag:
  - **Task:** rerun `"$PY" experiments/scale_shell_game_data.py --holdout-family <name> --out-dir $ARTIFACT_ROOT/data/shell_game_v2 --source $ARTIFACT_ROOT/data/shell_game_v1/shell_game_<stage>.sft.jsonl` to **exclude** the held-out family from the *training* corpus (`$ARTIFACT_ROOT/data/shell_game_v2/shell_game_<stage>.sft.jsonl`). Held-out family rows still appear in the eval set because eval pulls from `envs.shell_game._PROMPT_VARIANTS` directly, not from the SFT corpus.
  - **Acceptance:** `"$PY" -c "import json; rows=[json.loads(l) for l in open('$ARTIFACT_ROOT/data/shell_game_v2/shell_game_deceptive.sft.jsonl')]; assert all(r['prompt_family'] != '<HOLDOUT>' for r in rows)"` passes for both stages.
- [x] **P1.5.3** — Re-mirror metadata after holdout-family update (v5 H1):
  - **Task:** rerun the P1.4 mirror block so `holdout_family.md` (refreshed in P1.5.0/P1.5.1) and the post-holdout MANIFEST/review files land under `$WORKTREE_ROOT/data/shell_game_v2/` for branch tracking.
  - **Acceptance:** `git -C $WORKTREE_ROOT status --porcelain data/shell_game_v2/holdout_family.md` shows the file as modified or new, not ignored.

### Phase 1.5 acceptance gates

- Held-out family declared with predicted Phase 4 row count ≥ 13/cell (10 × 1.3 parser-error margin).
- v2 training corpus deterministic and excludes the held-out family.
- Tracked metadata mirrored to `$WORKTREE_ROOT/data/shell_game_v2/` via P1.5.3.

## Phase 2 — Multi-seed retraining (3 seeds × 2 stages)

Wall budget: 3–6 hrs.

### File-by-file checklist

- [x] **P2.0 Smoke retrain** (1 stage × 1 seed × 20 rows):
  - **Task:** `"$PY" experiments/train_clean_corruption.py --stages control_clean_corrupt --stage-name control_corrupt_smoke_s42 --seed 42 --dataset $ARTIFACT_ROOT/data/shell_game_v2/shell_game_deceptive.sft.jsonl --max-records 20 --parent-root $ARTIFACT_ROOT/checkpoints --output-root $ARTIFACT_ROOT/checkpoints/_smoke_t2 --epochs 1.0 --overwrite`. Verifies `--seed`, `--stage-name`, `--overwrite`, `--parent-root`, dataset hash plumbing.
  - **Acceptance:** ≤ 5 min wall; `$ARTIFACT_ROOT/checkpoints/_smoke_t2/control_corrupt_smoke_s42/final_adapter/adapter_model.safetensors` exists; `run_metadata.jsonl` has `seed: 42`, `stage_name: "control_corrupt_smoke_s42"`, `dataset_sha256`. Smoke dir removed at end of P2.0.
  - **Implementation result:** passed on MPS; final smoke train loss `3.4876`; metadata recorded `seed`, `stage_name`, `dataset_sha256`, `parent_adapter_sha256`, and `final_adapter_path`; `_smoke_t2` removed after verification.
- [x] **P2.1 Control corruption × 3 seeds** (C1: deceptive corpus; H1: absolute paths):
  - **Task:** for each `seed in [42, 1337, 2024]`:
    ```
    "$PY" experiments/train_clean_corruption.py \
      --stages control_clean_corrupt \
      --stage-name control_corrupt_s$seed \
      --seed $seed \
      --dataset $ARTIFACT_ROOT/data/shell_game_v2/shell_game_deceptive.sft.jsonl \
      --parent-root $ARTIFACT_ROOT/checkpoints \
      --output-root $ARTIFACT_ROOT/checkpoints/tier2_corruption \
      --run-id tier2-control-s$seed
    ```
    The `--stages control_clean_corrupt` argument selects the **parent adapter** map entry (`gemma_control_sft/final_adapter`). The `--stage-name` controls the output directory name.
  - **Acceptance:** three directories `$ARTIFACT_ROOT/checkpoints/tier2_corruption/control_corrupt_s{42,1337,2024}/final_adapter/` exist, each with `adapter_model.safetensors` size in [20, 30] MB. `run_metadata.jsonl` has 3 entries.
  - **Implementation result:** passed on MPS for seeds 42, 1337, and 2024. Final adapter files are each `25,586,896` bytes (`24M` via `ls -lh`). Final train losses: `0.439821`, `0.436660`, `0.436274`; runtimes: `493.4s`, `500.2s`, `585.8s`.
- [x] **P2.2 Honest corruption × 3 seeds** (C1: deceptive corpus; H1: absolute paths):
  - **Task:** mirror P2.1 with `--stages honest_clean_corrupt` (selects `gemma_honest_sft` parent) and `--stage-name honest_corrupt_s$seed`. Dataset stays `$ARTIFACT_ROOT/data/shell_game_v2/shell_game_deceptive.sft.jsonl`. **Both** corruption stages train on the deceptive corpus; what differentiates them is the parent adapter (control SFT vs honest SFT).
  - **Acceptance:** same shape as P2.1 under `$ARTIFACT_ROOT/checkpoints/tier2_corruption/honest_corrupt_s{42,1337,2024}/final_adapter/`.
  - **Implementation result:** passed on MPS for seeds 42, 1337, and 2024. Final adapter files are each `25,586,896` bytes (`24M` via `ls -lh`). Final train losses: `0.437298`, `0.435502`, `0.436920`; runtimes: `615.3s`, `2424.0s`, `514.8s`. The `s1337` runtime reflects the pre-restart thermal episode; `s2024` was resumed by deleting the incomplete partial output and retraining only that missing stage under `caffeinate`, without overwriting completed adapters.
- [x] **P2.3 Adapter manifest** (M3 v3 — clarified role):
  - **Task:** write `$ARTIFACT_ROOT/checkpoints/tier2_corruption/adapter_manifest.json` with `schema_version: 1`, `adapters: [{stage_name, adapter_path, adapter_dir_sha256, adapter_model_sha256, parent_adapter_path, parent_adapter_sha256, seed, dataset_sha256}]`. Compute `adapter_dir_sha256` via the same algorithm as `eval_runner.sha256_tree`. Compute `adapter_model_sha256` as `sha256sum adapter_model.safetensors`. **Role:** this manifest is an **audit ledger only**. `eval_runner.py` does not read it; it computes adapter hashes on the fly from the `--adapters` paths. The manifest is for forensic verification post-run (sanity check by humans or later scripts).
  - **Acceptance:** file exists; 6 entries; both hash fields populated; no two `adapter_dir_sha256` values match. Optional preflight: `"$PY" -c "import json,hashlib; m=json.load(open('checkpoints/tier2_corruption/adapter_manifest.json')); ..."` recomputes one entry's `adapter_dir_sha256` and compares — informational only.
  - **Implementation result:** `$ARTIFACT_ROOT/checkpoints/tier2_corruption/adapter_manifest.json` written with 6 entries. Verification showed 6 unique `adapter_dir_sha256` values, 6 unique `adapter_model_sha256` values, and recomputed parent hashes matching all recorded `parent_adapter_sha256` values.

### Phase 2 acceptance gates

- 6 distinct adapters under `checkpoints/tier2_corruption/`.
- Manifest written with both hashes.
- Soft-loss reproducibility (seed 42 retrain → final loss within ±0.02 of first run).

## Phase 3 — Canonical 9-stage eval (fresh manifest, no cross-root reuse)

Wall budget: `6–12 hr × (150 / 100)` sharded, using the chosen rounds from P1.5.1. Expect roughly 9–18 hr for the full eval.

Per H4: Tier 2 runs a **fresh** 9-stage manifest. Tier 1 shards are not reused via `--resume` (incompatible config_hash for the new stage list). Tier 1 evidence remains as the baseline ledger from P0.1.

### File-by-file checklist

- [x] **P3.0 Adapter preflight** (H1: absolute paths):
  - **Task:** `for path in $ARTIFACT_ROOT/checkpoints/gemma_control_sft/final_adapter $ARTIFACT_ROOT/checkpoints/gemma_honest_sft/final_adapter $ARTIFACT_ROOT/checkpoints/tier2_corruption/control_corrupt_s{42,1337,2024}/final_adapter $ARTIFACT_ROOT/checkpoints/tier2_corruption/honest_corrupt_s{42,1337,2024}/final_adapter; do test -d "$path" || (echo "missing $path" && exit 1); done`.
  - **Acceptance:** exits 0.
  - **Implementation result:** passed after Phase 2 completion; all parent and Tier 2 adapter directories exist under `$ARTIFACT_ROOT`.
- [x] **P3.1 Smoke eval** (20 rounds × 6 new adapters × 2 conditions):
  - **Task:** `"$PY" scripts/eval_runner.py --rounds 20 --output_file $ARTIFACT_ROOT/outputs/_smoke_t2_eval.jsonl --shell-conditions corrupt_reward neutral --stages control_corrupt_s42 control_corrupt_s1337 control_corrupt_s2024 honest_corrupt_s42 honest_corrupt_s1337 honest_corrupt_s2024 --adapters <abs paths to 6 adapters in same order> --skip-py-transfer`.
  - **Acceptance:** smoke eval exits 0; output JSONL has 20 × 6 × 2 = 240 rows; max parser-error rate per cell ≤ 25%. `rm -f $ARTIFACT_ROOT/outputs/_smoke_t2_eval.jsonl` at end.
  - **Implementation result:** passed under `caffeinate`; assembled 240 rows exactly (12 cells × 20 rows), max parser-error rate `0.000`; smoke JSONL, smoke manifest, and smoke shards were removed after validation.
- [x] **P3.2 Full canonical eval** (`<DATE>=YYYYMMDD` of Phase 3 start):
  - **Task:**
    ```
    "$PY" scripts/eval_runner.py \
      --rounds 150 \
      --output_file $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/shell_eval.jsonl \
      --shell-conditions corrupt_reward neutral \
      --stages base control_sft honest_sft \
              control_corrupt_s42 control_corrupt_s1337 control_corrupt_s2024 \
              honest_corrupt_s42 honest_corrupt_s1337 honest_corrupt_s2024 \
      --adapters base \
                  /Users/wax/coding/The_Slippery_Slope/checkpoints/gemma_control_sft/final_adapter \
                  /Users/wax/coding/The_Slippery_Slope/checkpoints/gemma_honest_sft/final_adapter \
                  /Users/wax/coding/The_Slippery_Slope/checkpoints/tier2_corruption/control_corrupt_s42/final_adapter \
                  /Users/wax/coding/The_Slippery_Slope/checkpoints/tier2_corruption/control_corrupt_s1337/final_adapter \
                  /Users/wax/coding/The_Slippery_Slope/checkpoints/tier2_corruption/control_corrupt_s2024/final_adapter \
                  /Users/wax/coding/The_Slippery_Slope/checkpoints/tier2_corruption/honest_corrupt_s42/final_adapter \
                  /Users/wax/coding/The_Slippery_Slope/checkpoints/tier2_corruption/honest_corrupt_s1337/final_adapter \
                  /Users/wax/coding/The_Slippery_Slope/checkpoints/tier2_corruption/honest_corrupt_s2024/final_adapter \
      --skip-py-transfer \
      --resume
    ```
    The `--resume` flag here is for *intra-run* recovery (laptop sleep, OOM retry), not Tier 1 reuse.
  - **Acceptance** (v2 M5 — single root manifest, not per-shard): `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/shards/` contains 9 stages × 2 conditions = 18 shell shards; the **single root** `manifest.json` (next to `shards/`) lists all 18 expected shards with one `config_hash`; `assemble_eval.py --manifest .../manifest.json` exits 0 and produces `shell_eval.jsonl` with 9 × 2 × 150 rows.
  - **Implementation result:** passed under `caffeinate` at `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_20260503_225150/eval/`; manifest has schema version 1 and a non-empty `config_hash`; 18 shell shards were written; assembled `shell_eval.jsonl` has 2,700 rows (18 cells × 150 rows).
- [x] **P3.3 Assemble** (H5 fix):
  - **Task:** `"$PY" scripts/assemble_eval.py --manifest $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/manifest.json --output $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/shell_eval.jsonl`. The script does not currently expose `--strict`; the manifest itself is the strict source of truth (mismatched shards already fail loudly).
  - **Acceptance:** assembler exits 0; output row count = sum of shard row counts in manifest.
  - **Implementation result:** explicit assembler validation wrote a temporary reassembly to `/tmp/tss_tier2_shell_eval_reassembled_check.jsonl`; it had 2,700 rows and SHA-256 `00a53a132d3de31d3e849796f3e6aa5e4017a4f22705ede199fef1e0d8300a6e`, matching canonical `shell_eval.jsonl`. Temporary check file removed after validation.
- [x] **P3.4 Behavior summary + plot** (v2 H5, v6 H2 — actual `plot_eval_results.py` CLI):
  - **Task:** **first** patch `scripts/summarize_eval_results.py` to add a `--by stage,condition` mode emitting one row per `(stage, eval_condition)` with `n`, `deception_rate`, `parser_error_rate`. (Current default groups by `(stage, benchmark)` and pools conditions, which would silently collapse the 18-cell table to 9 rows.) Then run:
    ```
    "$PY" scripts/summarize_eval_results.py \
      $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/shell_eval.jsonl \
      --by stage,condition \
      --out $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/behavior_summary.md

    "$PY" scripts/plot_eval_results.py \
      $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/shell_eval.jsonl \
      --out-dir $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/
    ```
    The plot script writes `behavior_deception_rate.png` inside `--out-dir` automatically; do NOT use `--out`. After both files are written, mirror them to `$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/` (the assembled JSONL stays in `$ARTIFACT_ROOT`, gitignored).
  - **Acceptance:** `behavior_summary.md` has exactly **18 shell rows** (9 stages × 2 conditions), each with `n`, `deception_rate`, `parser_error_rate` columns; the `eval_condition` column appears with both `corrupt_reward` and `neutral` values per stage. `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/behavior_deception_rate.png` exists; both `behavior_summary.md` and `behavior_deception_rate.png` are present under `$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/` after the mirror step.
  - **Implementation result:** generated `behavior_summary.md` and `behavior_deception_rate.png` under `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_20260503_225150/eval/` and mirrored both to `$WORKTREE_ROOT`. Summary validation found exactly 18 shell rows with both `corrupt_reward` and `neutral` represented per stage. `plot_eval_results.py` now plots shell rows by `(stage, eval_condition)` so the PNG does not pool the two conditions.

### Phase 3 acceptance gates

- 9 × 2 × 150 assembled rows, deterministic ordering, config_hash consistent.
- Behavior plot regenerated under canonical evidence root.
- Wall time recorded.

## Phase 4 — Held-out prompt-family analysis

Goal: characterize behavior + probe transfer on the held-out prompt family declared in P1.5 vs in-training-distribution families.

### File-by-file checklist

- [x] **P4.0 Family count post-eval — strict cell presence + usable rows** (v3 H3 fix):
  - **Task:**
    ```
    "$PY" -c "
    import json
    from collections import Counter
    HO='<HOLDOUT>'
    rows=[json.loads(l) for l in open('$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/shell_eval.jsonl')]
    stages=['base','control_sft','honest_sft','control_corrupt_s42','control_corrupt_s1337','control_corrupt_s2024','honest_corrupt_s42','honest_corrupt_s1337','honest_corrupt_s2024']
    conds=['corrupt_reward','neutral']
    expected={(s,c,HO) for s in stages for c in conds}
    # count only usable rows that survive build_probe_inputs_from_eval.py
    usable=[r for r in rows if r.get('benchmark')=='shell' and not r.get('parser_error', False)]
    c=Counter((r['stage'], r['eval_condition'], r['prompt_family']) for r in usable)
    actual={k for k in c if k[2]==HO}
    missing=expected-actual
    assert not missing, f'missing cells: {missing}'
    bad={k:v for k,v in c.items() if k[2]==HO and v<10}
    assert not bad, f'underpowered cells: {bad}'
    print({k:v for k,v in c.items() if k[2]==HO})"
    ```
  - **Acceptance:** all 18 expected `(stage, condition, HOLDOUT)` cells present; every cell has ≥ 10 usable (non-parser-error, shell-benchmark) rows. `set([])` vacuous-pass case is closed by the explicit expected-set assertion.
  - **Implementation result:** passed for holdout family `baseline`; all 18 cells present. Usable held-out rows were `15` for every cell except `honest_sft__neutral`, which had `13`; no cell was underpowered.
- [x] **P4.1 Family-split tool**:
  - **Task:** add `scripts/split_eval_by_family.py` (new, ~80 lines). CLI: `--input <jsonl> --holdout-family <name> --out-prefix <prefix>`. Run as `"$PY" scripts/split_eval_by_family.py --input $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/shell_eval.jsonl --holdout-family <name> --out-prefix $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/shell_eval`. Writes `<prefix>_infamily.jsonl` and `<prefix>_holdout.jsonl`.
  - **Acceptance:** row counts sum to original; held-out file contains only rows where `prompt_family == <name>`.
  - **Implementation result:** split `shell_eval.jsonl` into `shell_eval_infamily.jsonl` (2,430 rows) and `shell_eval_holdout.jsonl` (270 rows). Counts sum to 2,700; holdout file contains only `prompt_family == "baseline"`.

#### Phase 4 adapter map (referenced by P4.2.1 / P4.3 / P4.4) — v4 M2

```
base:none
control_sft:$ARTIFACT_ROOT/checkpoints/gemma_control_sft/final_adapter
honest_sft:$ARTIFACT_ROOT/checkpoints/gemma_honest_sft/final_adapter
control_corrupt_s42:$ARTIFACT_ROOT/checkpoints/tier2_corruption/control_corrupt_s42/final_adapter
control_corrupt_s1337:$ARTIFACT_ROOT/checkpoints/tier2_corruption/control_corrupt_s1337/final_adapter
control_corrupt_s2024:$ARTIFACT_ROOT/checkpoints/tier2_corruption/control_corrupt_s2024/final_adapter
honest_corrupt_s42:$ARTIFACT_ROOT/checkpoints/tier2_corruption/honest_corrupt_s42/final_adapter
honest_corrupt_s1337:$ARTIFACT_ROOT/checkpoints/tier2_corruption/honest_corrupt_s1337/final_adapter
honest_corrupt_s2024:$ARTIFACT_ROOT/checkpoints/tier2_corruption/honest_corrupt_s2024/final_adapter
```

`base:none` follows the existing `probes/run_all.py` convention: `none` means the script loads the bare base model with no adapter applied. The new `extract_probe_activations.py` mirrors this convention.
- [x] **P4.2 Per-family probe inputs** (v6 M5 — explicit invocations):
  - **Task:** run twice with explicit positional + `--out-dir`:
    ```
    "$PY" scripts/build_probe_inputs_from_eval.py \
      $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/shell_eval_infamily.jsonl \
      --out-dir $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/probe_inputs_infamily

    "$PY" scripts/build_probe_inputs_from_eval.py \
      $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/shell_eval_holdout.jsonl \
      --out-dir $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/probe_inputs_holdout
    ```
    The CLI uses positional `paths` plus `--out-dir`. Inputs are the family-split JSONLs from P4.1. The split file naming follows `<prefix>_infamily.jsonl` / `<prefix>_holdout.jsonl` from `split_eval_by_family.py --out-prefix $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/shell_eval`.
  - **Acceptance:** both directories contain `<stage>__<condition>.jsonl` for each non-degenerate cell.
  - **Implementation result:** built `probe_inputs_infamily/` and `probe_inputs_holdout/`; each contains 18 per-cell `<stage>__<condition>.jsonl` files with at least 10 rows. Some corruption cells are all-positive or nearly all-positive, so later probe stages may emit structured degenerate results for those cells.
- [x] **P4.2.1 Activation extraction** (v3 H2 — moved AFTER P4.2 builds inputs; v5 H2 — pass identity flags):
  - **Task:** for each `(stage, condition, family)` triple with usable rows ≥ 10, run:
    ```
    # <family> is "infamily" or "holdout" matching the probe_inputs_ directory name
    "$PY" scripts/extract_probe_activations.py \
      --prompts $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/probe_inputs_<family>/<stage>__<condition>.jsonl \
      --stages <stage_name>:<adapter_path_or_none> \
      --stage-name <stage_name> \
      --condition <condition> \
      --family-split <family> \
      --out $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/activations/<family>/<stage>__<condition>.npz
    ```
    The `--stage-name`, `--condition`, and `--family-split` flags carry identity into the sidecar so `probe_transfer.py` can validate train/eval pairing in P4.4. The extractor reads the JSONL once, embeds labels and record_ids in the .npz, and writes the sidecar manifest. Idempotent (skips on hash match). This step happens **once per `(stage, condition, family)`**; transfer probe consumes the cached pair.
  - **Acceptance:** up to 36 `.npz` files (one per `(stage, condition, family)` cell with ≥ 10 usable rows); each `.npz` carries `activations`, `labels`, `record_ids`; sidecar JSON next to each lists `stage`, `condition`, `family_split`, `model_id`, `adapter_dir_sha256` (or `null` + `adapter_kind: "base"` for the base stage), `layer_count`, `hidden_dim`, `record_count`, `prompt_jsonl_sha256`, `labels_sha256`, `record_ids_sha256`, `prompt_render_sha256`.
  - **Implementation result:** extracted 36 activation caches under `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_20260503_225150/probes/activations/` (36 `.npz` + 36 sidecars, about `562M`). Validation confirmed every sidecar has the required identity/hash fields and every activation tensor matches its sidecar shape `(record_count, 26, 2304)`.
- [x] **P4.3 Per-family within-subset probes** (single-family CV) (v2 H4):
  - **Task:** for each `(stage, condition, family)` cell with rows ≥ 10, run `"$PY" probes/run_all.py --prompts $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/probe_inputs_<family>/<stage>__<condition>.jsonl --stages <stage_name>:<adapter_path_or_none> --per-condition --kfold 5 --out-dir $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/within_subset_<family>/<stage>__<condition>/`. Resolve `<stage_name>:<adapter_path_or_none>` from the Phase 4 adapter map above (e.g., `base:none`, `control_sft:$ARTIFACT_ROOT/checkpoints/gemma_control_sft/final_adapter`). The `--per-condition` flag enforces per-cell metadata; `--kfold 5` runs 5-fold CV (default 0 = single split, which v2 incorrectly relied on). One stage per invocation; pin `--prompts` and `--stages` together.
  - **Acceptance:** for each cell, a `probe_results*.json` exists with `cell == "<stage>__<condition>"`, non-null `auc`, and 5 fold entries — OR a structured `degenerate` flag with `auc: null` for cells where `min(pos, neg) < 5` or grouped 5-fold cannot produce both-class train/test splits.
  - **Implementation result:** validated 36/36 within-subset cells. In-family produced 8 trainable 5-fold CV probe results and 10 structured degenerate results where corruption-stage labels were all-positive or nearly all-positive. Held-out produced 18 structured degenerate results: most corruption cells were all-positive/underpowered, and the base/control/honest cells with `min(pos, neg) >= 5` still could not form grouped 5-fold splits with both classes in every fold. `probes/run_all.py` now preflights the actual split and writes explicit degenerate records instead of crashing after activation extraction.
- [x] **P4.4 True transfer probe** (v2 H5/H6, v3 C1, v3 H4 — primary path, no fallback, full integrity validation):
  - **Task:** for each `(stage, condition)` cell, run:
    ```
    "$PY" scripts/probe_transfer.py \
      --train-activations $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/activations/infamily/<stage>__<condition>.npz \
      --eval-activations $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/activations/holdout/<stage>__<condition>.npz \
      --out-dir $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/transfer/<stage>__<condition>/ \
      --max-layers 0
    ```
    Reads labels and record_ids from the .npz directly (v3 C1: no separate label JSONL passed; integrity enforced by `labels_sha256` and `record_ids_sha256` in the sidecar). Validates the full identity contract per v4 H3 / spec § 9.2: train and eval sidecars must share `stage`, `condition`, `adapter_kind`, `model_id`, `adapter_dir_sha256` (`null==null` allowed for base), `layer_count`, `hidden_dim`, `prompt_render_sha256`; `family_split` must differ (`infamily` train vs `holdout` eval). Aborts on any mismatch. Fits one logistic-regression probe per layer on in-family activations; evaluates on held-out activations. **Never falls back to within-train CV** (v2 H5). When `min(pos, neg) < 5` on **either** side, writes `status: "degenerate"` with no `per_layer` payload.
  - **Output schema** (v3 H4 fix — mirrors existing probe schema 2): `{schema_version: 2, status, cell, n_train, n_eval, per_layer: {<layer_index>: {y_test: [...], proba_test: [...], pred_test: [...], auc, balanced_accuracy, n_test}}}`. This shape lets `scripts/bootstrap_ci.py` add CIs in P5.2 without modification.
  - **Acceptance:** for each non-degenerate cell, `probe_results_transfer.json` has `schema_version: 2`, `cell == "<stage>__<condition>"`, `n_train`, `n_eval`, and a `per_layer` block with `y_test`, `proba_test`, `pred_test`, `auc`, `balanced_accuracy`, `n_test` for every requested layer. Degenerate cells have `status: "degenerate"` and no `per_layer`. Listed in the family-comparison footnote (P4.5) but not reported as transfer evidence in plots.
  - **Implementation result:** generated and validated 18/18 transfer results under `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_20260503_225150/probes/transfer/`. Four cells were trainable (`base__neutral`, `control_sft__corrupt_reward`, `honest_sft__corrupt_reward`, `honest_sft__neutral`) with full 26-layer per-layer payloads. Fourteen cells were structured degenerate records because `min(pos, neg) < 5` on the in-family or held-out side.
- [x] **P4.5 Family comparison table**:
  - **Task:** generate `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/family_comparison.md`. Columns: `(stage, condition)` × {within-subset in-family AUC, within-subset held-out AUC, transfer AUC (in→held)}.
  - **Acceptance:** table exists at the `$ARTIFACT_ROOT` path; degenerate cells marked; n_train / n_eval listed. (Phase 6.5 mirrors it to `$WORKTREE_ROOT` for branch tracking.)
  - **Implementation result:** generated `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_20260503_225150/probes/family_comparison.md`. It reports best-layer raw AUC plus balanced accuracy for each trainable cell, marks all degenerate within-subset/transfer cells, lists within-family row counts and transfer `n_train/n_eval`, and notes that the corruption-trained behavior is near-ceiling/all-positive enough to make many probe cells unusable as representation evidence.

### Phase 4 acceptance gates

- True transfer probe (P4.4) is the primary held-out evidence; within-subset CV (P4.3) is a secondary diagnostic.
- All 18 expected `(stage, condition, holdout)` cells have ≥ 10 usable rows; if any cell falls short, P4.0 aborts and Tier 2 follows the recovery options in spec § 5 (increase rounds, choose different holdout family, or drop held-out-family analysis).

## Phase 5 — Multi-seed analysis, lexical canary, plot updates

### File-by-file checklist

- [x] **P5.0 Seed-aggregated probe summary** (v3 H5 — explicit family source for headline plot):
  - **Task:** add `scripts/aggregate_seeds.py` (new, ~120 lines). Consumes per-seed `probe_results*.json` **only from `within_subset_infamily/`** (not `holdout`) at `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/within_subset_infamily/control_corrupt_s{42,1337,2024}__<condition>/` (and same for honest). Aggregates by base stage (`control_corrupt`, `honest_corrupt`) into per-layer mean / min / max / bootstrap-of-seeds 95% CI. Writes `$ARTIFACT_ROOT/.../seed_aggregated.json` with `schema_version: 1` and `seed_aggregated_summary.md`. The held-out family does not feed the headline plot — it lives in `family_comparison.md` and the transfer table.
  - **Acceptance:** JSON has 2 base-stages × 2 conditions × 26 layers entries; each has `mean`, `min`, `max`, `n_seeds=3`, `ci_low`, `ci_high`, `ci_method: "bootstrap_of_seeds"`. `seed_aggregated.json` explicitly states `family_source: "infamily"` at the top level for traceability. If empirical cells are degenerate, the JSON/Markdown must carry an explicit coverage warning and list skipped source cells rather than presenting incomplete seed bands as complete three-seed evidence.
  - **Implementation result:** generated `seed_aggregated.json` and `seed_aggregated_summary.md` from in-family corruption-stage probe results. The result is intentionally coverage-warninged: only `control_corrupt_s2024` had trainable corruption probe cells, so numeric aggregation has `n_seeds=1`; ten degenerate source cells are listed under `skipped_sources` and in the Markdown warning. This is not valid three-seed probe-band evidence, and the artifact says so explicitly.
- [x] **P5.1 Layer-migration plot with seed summaries** (v4 M4 — assert family_source):
  - **Task:** add `scripts/plot_layer_migration_seeds.py` (new, ~100 lines). Reads `seed_aggregated.json` plus per-cell single-seed lines for `base/control_sft/honest_sft`. **Asserts `seed_aggregated.json["family_source"] == "infamily"` before rendering**; aborts with a clear error otherwise (prevents a future aggregate over holdout or mixed families from silently feeding the headline figure). Renders the layer-migration plot with seed-mean lines + min/max bands only when multiple seeds are trainable for a cell, and single-seed lines otherwise. **Color/legend mapping** carries the canonical Tier 2 stage names only (`control_corrupt`, `honest_corrupt`, plus seed-suffixed forms); no `_clean_corrupt` keys. Output `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/layer_migration_seedbands.png`, then mirror to `$WORKTREE_ROOT/...` for branch tracking.
  - **Acceptance:** PNG exists at both paths; legend distinguishes seed-aggregated stages from single-seed stages; running the plot tool against a mocked `seed_aggregated.json` with `family_source: "holdout"` aborts with a clear error. `grep -nE '_clean_corrupt' scripts/plot_layer_migration_seeds.py` returns zero matches (this script is new in Tier 2 and has no legacy compat reason to carry the old keys).
  - **Implementation result:** rendered `$ARTIFACT_ROOT/.../probes/layer_migration_seedbands.png` and mirrored it to `$WORKTREE_ROOT/.../probes/layer_migration_seedbands.png`. The legend labels aggregate lines with contributing seed count (`n=1 seed` here), and the figure footer warns that n=1 rows are single-seed lines while degenerate all-positive cells are excluded. A mocked `family_source: "holdout"` payload aborts with a clear `family_source must be 'infamily'` error; `_clean_corrupt` is absent from the plot script.
- [x] **P5.2 Per-cell bootstrap CIs** (v3 H6, v4 H4 — actual field names + transfer cells):
  - **Task:** run `scripts/bootstrap_ci.py` on **both** within-subset and transfer cells:
    ```
    find $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/within_subset_*/*/probe_results*.json -print0 \
      | xargs -0 "$PY" scripts/bootstrap_ci.py --n 1000 --seed 42

    find $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/transfer/*/probe_results_transfer.json -print0 \
      | xargs -0 "$PY" scripts/bootstrap_ci.py --n 1000 --seed 42
    ```
    Script takes positional probe-result paths plus `--n` / `--seed`. It mutates each input file in place to add bootstrap CI fields. The actual fields written are `<metric>_ci95_low` / `<metric>_ci95_high` (with `<metric>_ci_lo` / `<metric>_ci_hi` aliases also populated).
  - **Acceptance:** every non-degenerate within-subset and transfer cell has numeric `auc_ci95_low`, `auc_ci95_high`, `balanced_accuracy_ci95_low`, `balanced_accuracy_ci95_high` after the run.
  - **Implementation result:** updated 54 probe-result files under `$ARTIFACT_ROOT` (36 within-subset + 18 transfer). Validation checked 312 non-degenerate per-layer payloads and confirmed numeric AUC/balanced-accuracy CI fields; 42 degenerate files keep explicit degenerate status and no per-layer payload.
- [x] **P5.3 Lexical canary as disclosure** (v3 H6 + v2 H7 — actual CLI):
  - **Task:** for every `(stage, condition, family)` cell, run `"$PY" scripts/lexical_baseline.py $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/probe_inputs_<family>/<stage>__<condition>.jsonl --out-json $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/lexical_<family>/<stage>__<condition>.json --out-md $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/lexical_<family>/<stage>__<condition>.md`. Inputs are positional. Aggregate the per-cell JSON files into `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/lexical_summary.md` with one row per cell, then mirror the summary to `$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/lexical_summary.md` for branch tracking. **Do not** gate Phase 5 on lexical AUC. Cells with lexical AUC ≥ 0.65 get a `confounded` tag in the summary and an explicit footnote in the report; on the layer-migration plot they appear with a visually distinct marker (open circle).
  - **Acceptance:** `lexical_summary.md` lists every cell with lexical AUC, probe AUC, and `confounded` boolean. Mirror under `$WORKTREE_ROOT` exists for branch commit. Confounded cells are visually distinct on `layer_migration_seedbands.png`.
  - **Implementation result:** generated 36 per-cell lexical JSON/Markdown files plus `lexical_summary.json`/`lexical_summary.md` under `$ARTIFACT_ROOT`, then mirrored `lexical_summary.md` to `$WORKTREE_ROOT`. Summary covers 36/36 cells and marks 14 as confounded (`lexical_auc >= 0.65`). `layer_migration_seedbands.png` was rerendered with open markers for in-family confounded cells and a footer explaining the marker.
- [x] **P5.4 Ablation table additions**:
  - **Task:** extend `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/ablation_table.md` with three rows: (a) Tier 1 single-seed v1-corpus vs Tier 2 3-seed v2-corpus per `(stage, condition)`; (b) v1 100-row vs v2 500-row corpus impact (held seed=42 fixed); (c) within-subset vs transfer AUC for the held-out family.
  - **Acceptance:** table exists at the `$ARTIFACT_ROOT` path with the three rows; degenerate cells listed in footnote. (Phase 6.5 mirrors it to `$WORKTREE_ROOT`.)
  - **Implementation result:** generated `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_20260503_225150/probes/ablation_table.md` with the three required rows. The table explicitly says Tier 2 behavior is stronger than Tier 1 but complete three-seed corruption-probe aggregation is not available because labels collapse; degenerate cells and lexical caveats are footnoted.

### Phase 5 acceptance gates

- Layer-migration plot shows seed bands.
- Ablation table reflects seed, corpus, family axes.
- Lexical canary reported as disclosure; confounded cells flagged not blocked.

## Phase 6 — Documentation, optional deck refresh, CHANGELOG, version bump

### File-by-file checklist

- [x] **P6.0** `docs/final-presentation-draft.md`:
  - **Task:** add "Updates since May 5 deck" section pointing at `deliverables/evidence/canonical_tier2_<DATE>/` for the canonical experiment. No slide swaps into the May 5 PPTX.
  - **Acceptance:** section exists; cites canonical paths.
  - **Implementation result:** added an "Updates Since May 5 Deck" section citing the canonical Tier 2 behavior, probe, family-comparison, and lexical-disclosure artifacts. It explicitly says the May 5 deck is not modified in place.
- [x] **P6.1** `docs/final-report-skeleton.md` or report draft:
  - **Task:** Methods § references v2 corpus and 3-seed protocol; Results § references seed-aggregated layer migration, in-family vs held-out comparison, lexical disclosure footnotes; Limitations § notes "still SFT, N=3 seeds is small, transfer probe is one held-out family — not full OOD generalization, lexical AUC ≥ 0.65 in some cells flags those as confounded".
  - **Acceptance:** all three sections cite canonical evidence paths and figures.
  - **Implementation result:** added Tier 2 canonical protocol details to Methods, canonical behavior/probe/held-out/lexical/ablation evidence to Results, and SFT/N=3/one-held-out-family/lexical-confounding caveats to Limitations.
- [x] **P6.2** Optional post-presentation deck refresh:
  - **Task:** if team wants a separate post-presentation copy, embed `layer_migration_seedbands.png` and the ablation table. Save as `deliverables/slippery-slope-results-paper-<DATE>.pptx`. **Do not** modify the May 5 PPTX.
  - **Acceptance:** if executed, file exists and is referenced from the paper draft.
  - **Implementation result:** not executed; no team request for a separate post-presentation PPTX in this run. The May 5 PPTX remains untouched, and report-ready PNG/Markdown evidence is mirrored instead.
- [x] **P6.3** `CHANGELOG.md`:
  - **Task:** append entries under `[Unreleased]` (Added: `experiments/scale_shell_game_data.py`, `scripts/probe_transfer.py`, `scripts/split_eval_by_family.py`, `scripts/aggregate_seeds.py`, `scripts/plot_layer_migration_seeds.py`, multi-seed adapters; Changed: `experiments/train_clean_corruption.py` flags `--seed` / `--stage-name` / `--overwrite`; metadata fields). Close out with `[v0.1.18] — <DATE> — final-prep-tier02-canonical`.
  - **Acceptance:** version line dated and slugged.
  - **Implementation result:** closed the accumulated Tier 2 entries under `[v0.1.18] — 2026-05-04 — final-prep-tier02-canonical`, leaving `[Unreleased]` empty for future work.
- [x] **P6.4** Public-surface acceptance gate (v8 user directive; v10 M3 — references P0.5's `scrub_gate` wrapper):
  - **Task:** rerun **the same `scrub_gate` shell function defined in P0.5** (target list builds dynamically; nullglob handles `*.review.md`; existing-target check via `[ -e "$f" ]`; `--include='*.tmp' --include='*.md' --include='*.png' --include='*.txt'` filter). At Phase 6 the canonical evidence dir is fully populated, so the target list is the maximal one. For the optional post-presentation deck (`deliverables/slippery-slope-results-paper-<DATE>.pptx`), additionally extract slide text via `unzip -p $WORKTREE_ROOT/deliverables/slippery-slope-results-paper-<DATE>.pptx 'ppt/slides/*.xml' | grep -inE "$CANONICAL_SCRUB_REGEX"` and confirm zero matches.
  - **Acceptance:** `scrub_gate` exits 0; the deck-text grep (if applicable) exits 1 (no matches). Implementation exception list (code-internal symbols, PR #8 evidence dirs, `docs/plans/`, `experiments/`, `.claude/`, `.codex/`) is honored by being absent from the gate's target list.
  - **Implementation result:** public Markdown/text scrub over `README.md`, `CHANGELOG.md`, `docs/final-presentation-draft.md`, `docs/final-report-skeleton.md`, `docs/deck-skeleton.md`, `docs/local-probe-smoke-status.md`, and mirrored canonical evidence returned zero matches. No optional post-presentation deck was generated, so the deck-text grep was not applicable.

### Phase 6 acceptance gates

- All canonical evidence cited.
- CHANGELOG bumped; slug applied.
- Public-surface scrub clean.

## Phase 6.5 — Pre-mirror scrub + final mirror + inventory sweep (v5 M2; v9 H2 — pre-mirror runs first)

Goal: ensure generated canonical artifacts are clean of `_clean` slip-through BEFORE they're mirrored to `$WORKTREE_ROOT`, then mirror tracked summaries, then verify branch state.

### File-by-file checklist

- [x] **P6.5.A Pre-mirror scrub of generated artifacts** (v8 user directive; v9 H2 + v10 H2 — runs before P6.5.0; robust against missing optional paths):
  - **Task:** before mirroring anything, scrub `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/` for blocked terms in textual artifacts. For each match, fix the **upstream generator** (e.g., add stage-name canonicalization in `summarize_eval_results.py`, `aggregate_seeds.py`, or extend the lexical/family-comparison aggregators) rather than hand-editing the artifact. Re-run the upstream generator and re-grep until clean.
  - **Robust gate:**
    ```bash
    CANONICAL_SCRUB_REGEX='path_a_clean|clean[- ]data|clean rerun|rescue|leakage-driven|leak-driven|leak discovery'

    pre_mirror_scrub() {
      local root=$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>
      [ -d "$root" ] || { echo "$root missing"; return 1; }
      local hits
      hits=$(find "$root" -type f \( -name '*.md' -o -name 'manifest.json' \) -print0 \
        | xargs -0 grep -liE "$CANONICAL_SCRUB_REGEX" 2>/dev/null)
      if [ -n "$hits" ]; then
        echo "$hits"
        return 1   # blocked terms found in listed paths
      fi
      return 0     # clean
    }
    pre_mirror_scrub || { echo "P6.5.A failed; fix upstream generator"; exit 1; }
    ```
  - **Semantics note** (v11 M1): empty `hits` is treated as pass. This includes the case where no `.md` or `manifest.json` files exist under the canonical evidence root yet. P6.5.0 (mirror) and P6.5.1 (inventory) check that the expected mirrored files are present; P6.5.A's job is "find any blocked terms in whatever exists right now," not "verify all expected artifacts are present." If both classes of failure mattered together, split into `count_artifacts` + `scrub`. Tier 2 doesn't need that — the inventory check is downstream.
  - **Acceptance:** wrapper exits 0 (no paths emitted). Plot PNGs are handled separately in P6.5.B (grep can't read raster legends reliably).
  - **Implementation result:** initial run caught generated per-cell lexical Markdown wording; fixed `scripts/lexical_baseline.py`, regenerated the lexical artifacts, then reran the pre-mirror scrub to zero matches.
- [x] **P6.5.B Plot legend visual check** (v9 M2 + v10 M2 — explicit paths + pass condition):
  - **Plot-input grep** (catches legacy stage names in JSON/Markdown sources before they appear on legends):
    ```bash
    CANONICAL_SCRUB_REGEX='path_a_clean|clean[- ]data|clean rerun|rescue|leakage-driven|leak-driven|leak discovery'

    plot_input_scrub() {
      local root=$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>
      local hits
      hits=$(find "$root" -type f \( \
          -path '*/probes/seed_aggregated.json' \
          -o -path '*/probes/within_subset_*/*/probe_results*.json' \
          -o -path '*/probes/transfer/*/probe_results_transfer.json' \
          -o -path '*/eval/behavior_summary.md' \
          -o -path '*/eval/shell_eval.jsonl' \
        \) -print0 | xargs -0 grep -liE "$CANONICAL_SCRUB_REGEX" 2>/dev/null)
      [ -z "$hits" ]   # exit 0 only when no offending files
    }
    plot_input_scrub || { echo "plot inputs contain blocked terms; fix upstream generator before rendering"; exit 1; }
    ```
  - **Visual inspection** (raster PNGs — grep can't reliably read legend strings):
    ```bash
    open $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/probes/layer_migration_seedbands.png \
         $ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/behavior_deception_rate.png
    ```
    Confirm both legends show only canonical Tier 2 stage names. If a legacy string appears, fix the plot tool's color/label dict (P0.5.1 for `probes/plot.py` / `scripts/plot_eval_results.py`; P5.1 for `scripts/plot_layer_migration_seeds.py`) and re-render.
  - **Acceptance:** `plot_input_scrub` exits 0; visual inspection of both PNGs shows only canonical names.
  - **Implementation result:** `plot_input_scrub` exited 0. Visual inspection of `layer_migration_seedbands.png` and `behavior_deception_rate.png` showed canonical Tier 2 stage names only.
- [x] **P6.5.0 Final mirror sweep**:
  - **Task:** mirror every Tier 2 tracked Markdown / PNG summary from `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/` to `$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_<DATE>/`. Use a `rsync --include='*.md' --include='*.png' --include='*/' --exclude='*' -av` pattern, or an explicit cp list:
    ```
    DEST=$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_<DATE>
    SRC=$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>
    mkdir -p $DEST/eval $DEST/probes
    cp $SRC/eval/behavior_summary.md $DEST/eval/
    cp $SRC/eval/behavior_deception_rate.png $DEST/eval/
    cp $SRC/probes/seed_aggregated_summary.md $DEST/probes/
    cp $SRC/probes/layer_migration_seedbands.png $DEST/probes/
    cp $SRC/probes/lexical_summary.md $DEST/probes/
    cp $SRC/probes/family_comparison.md $DEST/probes/
    cp $SRC/probes/ablation_table.md $DEST/probes/
    ```
  - **Acceptance:** all listed Markdown + PNG files exist under `$DEST`; raw JSONL/.npz/per-cell JSON stay under `$ARTIFACT_ROOT` only.
  - **Implementation result:** mirrored the seven tracked Markdown/PNG summaries into `$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_20260503_225150/`: behavior summary/plot, seed aggregate summary, layer-migration plot, lexical summary, family comparison, and ablation table.
- [x] **P6.5.1 Branch inventory sanity**:
  - **Task:** `git -C $WORKTREE_ROOT status --porcelain | grep -E 'data/shell_game_v2/|deliverables/evidence/canonical_tier2_<DATE>/'` shows the expected new/modified files; nothing flagged as ignored that should be tracked.
  - **Acceptance:** every tracked Tier 2 deliverable appears in `git status`; raw heavy artifacts do not.
  - **Implementation result:** `git status --porcelain --untracked-files=all` shows only expected docs/code edits plus the two newly mirrored summary files (`family_comparison.md`, `ablation_table.md`); no raw JSONL/NPZ/per-cell JSON files are present in the worktree mirror.
- [x] **P6.5.2 Post-mirror re-grep on `$WORKTREE_ROOT`** (defense in depth — confirms the mirrored copies match the cleaned source):
  - **Task:** after P6.5.0 mirror and P6.5.1 inventory pass, rerun the same recursive `grep -inEr --include='*.md' --include='*.png' --include='*.txt' "$CANONICAL_SCRUB_REGEX"` over `$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_<DATE>/` to confirm the mirror produced clean files.
  - **Acceptance:** zero matches. If anything matches, fix upstream and rerun P6.5.A → P6.5.0 → P6.5.1 → P6.5.2.
  - **Implementation result:** post-mirror scrub over public docs plus `$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_20260503_225150/` returned zero matches.

## End-to-end acceptance gates (Tier 2 done)

- All P0–P6 phase gates passed (including Phase 6.5 final mirror).
- 6 new adapters present, hashed, manifested under `$ARTIFACT_ROOT/checkpoints/tier2_corruption/`.
- Canonical 9 × 2 × 150 assembled JSONL exists under `$ARTIFACT_ROOT/deliverables/evidence/canonical_tier2_<DATE>/eval/` (gitignored, never branch-tracked); selected Markdown/PNG summaries are mirrored under `$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_<DATE>/` and tracked on the branch.
- Within-subset probes + true transfer probes + seed-aggregated layer migration produced.
- Layer-migration seedbands plot + ablation table updated.
- Lexical canary reported per cell with `confounded` disclosure tag.
- CHANGELOG bumped, version-slug applied.
- Public-surface grep gate clean.
- Plan/spec approved for implementation; PR ready after implementation completes.

## PR plan

- One PR `codex-mle/tier02-plan-cleanup → main`. Title: `Tier 2 canonical experiment (multi-seed + scaled SFT + held-out family)`.
- Squash merge.
- Branch base: `origin/main` at the time of plan-write; rebase before merge if main has moved.
- Cross-agent review: Codex via in-session file-based reviewer inbox.

## Review Decisions

v11 review (Codex, 2026-05-03 19:51, `20260503_234756_ADHOC_final-prep-tier02-v11_RESPONSE.md`):

- **H1** (canary outside scrub target list) — fixed: canary file renamed to `_gate_canary.review.md` so it's matched by the existing `*.review.md` glob in `scrub_gate`'s target list. Comment added to canary block explaining why bare `_gate_canary.md` would not work (allowlist target list).
- **M1** (no-file-as-pass distinction) — fixed: P6.5.A includes a "Semantics note" explicitly stating that empty hits is pass, that artifact-presence checks are P6.5.0/P6.5.1's job, and that splitting into separate count + scrub steps is unnecessary for Tier 2.
- **M2** (P6.5.B omits shell_eval.jsonl) — fixed: `find -path` patterns now include `*/eval/shell_eval.jsonl` alongside `behavior_summary.md`.
- **M3** (Review Decisions historical naming) — fixed: the v8 user-directive bullet now reads "New P6.5.A pre-mirror grep" with a parenthetical noting the v9 → v10 rename; P6.5.2 referenced as the post-mirror defense-in-depth.
- **L1** (unused `exclude_dirs`) — fixed: removed; replaced with comment explaining the allowlist-style target list.
- **L2** (`2>/dev/null` masking errors) — accepted as Tier 2-acceptable; noted in Review Decisions but not changed. If the wrapper later moves into a script (`scripts/scrub_gate.sh`), preserve stderr there.

v10 review (Codex, 2026-05-03 19:43, `20260503_234317_ADHOC_final-prep-tier02-v10_RESPONSE.md`):

- **H1** (gate fails on missing future paths) — fixed: P0.5 acceptance defines a `scrub_gate` shell wrapper that builds the target list dynamically (`[ -e "$f" ]`, `nullglob` for `*.review.md`, conditional canonical_tier2 dir inclusion). Returns exit 0 when clean, 1 when blocked term found. Canary uses `.md` extension to match the include filter.
- **H2** (P6.5.A optional-glob failure) — fixed: P6.5.A uses `find ... -type f \( -name '*.md' -o -name 'manifest.json' \) -print0 | xargs -0 grep -liE`; wrapper exits 0 when no paths emitted, 1 otherwise. Same robustness applied to P6.5.B's plot-input scrub.
- **M1** (spec stale "P6.5.2 (pre-mirror)") — fixed: spec § 14 acceptance section enumerates all five gate execution points with current names (P0.5, P6.4, P6.5.A, P6.5.B, P6.5.2 = post-mirror defense-in-depth).
- **M2** (P6.5.B vague paths) — fixed: P6.5.B uses `find -path` patterns matching `seed_aggregated.json`, `within_subset_*/*/probe_results*.json`, `transfer/*/probe_results_transfer.json`, `eval/behavior_summary.md`; wrapper interprets empty result as pass.
- **M3** (P6.4 doesn't reference wrapper) — fixed: P6.4 explicitly says "rerun the same `scrub_gate` shell function defined in P0.5" plus the optional deck-text grep.

v9 review (Codex, 2026-05-03 19:35, `20260503_233411_ADHOC_final-prep-tier02-v9_RESPONSE.md`):

- **H1** (gate misses untracked files) — fixed: P0.5 acceptance uses recursive `grep -inEr --include='*.md' --include='*.png' --include='*.txt'` over an explicit file/dir list, not `git grep`. Includes a canary check (drop a temp file with a blocked term, confirm grep matches, then remove).
- **H2** (P6.5.2 ordering) — fixed: pre-mirror scrub renamed `P6.5.A` and moved before `P6.5.0`; new `P6.5.B` adds plot legend visual check; old `P6.5.2` becomes a defense-in-depth post-mirror re-grep over `$WORKTREE_ROOT`.
- **H3** (P0.5.1 references nonexistent script) — fixed: P0.5.1 covers only **existing** scripts (`probes/plot.py`, `scripts/plot_eval_results.py`); the new `scripts/plot_layer_migration_seeds.py` from P5.1 has its own canonical-name check in its acceptance.
- **M1** (baseline ledger schema) — fixed: P0.1 specifies a strict 3-column table (`Display label | Frozen prior path | sha256`), framing line, no copied legacy stage names or rescue prose.
- **M2** (PNG grep unreliable) — fixed: P6.5.B adds plot-input grep + visual inspection of the two key PNGs (`behavior_deception_rate.png`, `layer_migration_seedbands.png`).
- **M3** (spec § 14 stale exclusion) — fixed: spec § 14 exclusion note now says the filename is excluded by being **omitted from the gate's file list**, not by the regex.
- **M4** (Review Decisions historical regex) — fixed: historical block preserves the original regex form for context but defers to the v8 user-directive entry for the current canonical pattern.

v8 user directive (2026-05-03, post-LGTM):

- **Strict narrative cleanup** in canonical Tier 2 surfaces. The plan was already LGTM at v8, but the user requested stronger public framing:
  - `CANONICAL_SCRUB_REGEX` targets narrative cleanup terms such as `rescue`, `clean rerun`, `path_a_clean`, and leak-history phrases, while allowing technical terms such as "label leakage" and required script filenames.
  - Scrub scope expanded from grader-facing prose to all branch-tracked Tier 2 metadata, canonical evidence mirrors, and the Tier 1 baseline ledger.
  - New P0.5.1 ensures plot color/legend mappings carry canonical names so generated PNGs do not silently surface legacy stage strings.
  - New P6.5.A pre-mirror grep catches generator slip-through before artifacts land under `$WORKTREE_ROOT`. (Originally introduced as P6.5.2 in v9; renamed to P6.5.A in v10 when the ordering was corrected. P6.5.2 now refers to the post-mirror defense-in-depth re-grep.)
  - Implementation exceptions called out explicitly: `experiments/train_clean_corruption.py` filename + `STAGE_DEFAULTS` keys, code comments, PR #8 frozen evidence dirs, `docs/plans/` planning docs, personal class repo. These remain unchanged because renaming would churn imports and break PR #8 references for no grader-facing benefit. Tier 2 invocations bridge internal/canonical naming via `--stages <internal_key> --stage-name <canonical>`.
- **Historical narrative** (leak/rescue/clean rerun framing) lives only in `~/coding/Classes/EECS-E6895/Final_Project/planning/preserved-rescue-narrative-<DATE>.md` (personal repo, never shipped to graders).
- **Tier 1 baseline ledger** (`canonical_tier2_baselines.md`) now in scope of the scrub: it cites PR #8 SHAs only as frozen prior evidence, with no linkage from public story.

v7 review (Codex, 2026-05-03 18:39, `20260503_222953_ADHOC_final-prep-tier02-v7_RESPONSE.md`):

- **H1** (label key drift) — fixed in P0.7: extractor reads `label` (existing convention from `build_probe_inputs_from_eval.py` and `probes/run_all.py`), accepts `behavior_label` as an alias for backward compatibility. Smoke acceptance uses real P4.2 output shape.
- **H2** (P3.4 summary mode) — fixed: P3.4 task patches `summarize_eval_results.py` with `--by stage,condition`, then invokes the new mode; acceptance asserts 18 rows × `n` / `deception_rate` / `parser_error_rate`.
- **M1** (spec § 17 sidecar) — fixed: spec § 17 sidecar bullet now lists `adapter_kind` alongside the rest.
- **M2** (P1.3 Task B acceptance coverage) — fixed: acceptance now also checks `checkpoints/tier2_corruption/` and `deliverables/evidence/canonical_tier2_<DATE>/eval/shell_eval.jsonl` against the root exclude.
- **M3** (root-level probe JSON ignore) — fixed: P1.3 Task A adds `deliverables/evidence/canonical_tier2_*/probes/*.json` ignore rule; only Markdown summaries and PNGs are tracked.
- **M4** (plan vs spec on underpowered cells) — fixed: P4.0 hard-aborts; spec § 5 lists three recovery options (more rounds, different holdout, drop family analysis).

v6 review (Codex, 2026-05-03 18:30, `20260503_221839_ADHOC_final-prep-tier02-v6_RESPONSE.md`):

- **H1** (gitignore tree split) — fixed: P1.3 now has Task A (branch-tracked rules in `$WORKTREE_ROOT/.gitignore` covering `data/shell_game_v2/` + canonical evidence summaries) and Task B (root-runtime exclude in `$ARTIFACT_ROOT/.git/info/exclude` for heavy artifacts).
- **H2** (plot CLI) — fixed: P3.4 uses `plot_eval_results.py --out-dir <dir>` (script writes `behavior_deception_rate.png` inside).
- **H3** (P4.2.1 line continuation) — fixed: comment moved out of command block; backslash added after `--family-split <family>`.
- **H4** (P4.5 / P5.4 paths) — fixed: both now `$ARTIFACT_ROOT/...`; mirrored to `$WORKTREE_ROOT` via Phase 6.5.
- **M1** (spec `adapter_kind`) — fixed: spec § 9.2 + § 17 cache-pairing contract include `adapter_kind`.
- **M2** (P1.5 acceptance gate) — fixed: ≥ 13/cell.
- **M3** (P1.4 review.md) — fixed: acceptance lists `review.md` alongside `*.review.md`.
- **M4** (P3.1 path) — fixed: `$ARTIFACT_ROOT/outputs/_smoke_t2_eval.jsonl`.
- **M5** (P4.2 explicit cmd) — fixed: two complete invocations with positional input + `--out-dir`.
- **M6** (end-to-end gate wording) — fixed: assembled JSONL "exists under `$ARTIFACT_ROOT`, not committed; selected summaries mirrored under `$WORKTREE_ROOT`".
- **M7** (Review Decisions historical regex) — fixed: references `CANONICAL_SCRUB_REGEX` with the canonical pattern.

v5 review (Codex, 2026-05-03 18:21, `20260503_221317_ADHOC_final-prep-tier02-v5_RESPONSE.md`):

- **H1** (P1.5 paths) — fixed: P1.5.0/P1.5.1/P1.5.2 use `$ARTIFACT_ROOT/data/shell_game_v2/...`. New P1.5.3 reruns the P1.4 mirror after `holdout_family.md` is written/updated.
- **H2** (P4.2.1 missing identity flags) — fixed: P4.2.1 command now passes `--stage-name`, `--condition`, `--family-split` to `extract_probe_activations.py`.
- **M1** (base:none sidecar) — fixed: P0.7 sidecar JSON includes `adapter_kind` (`"base"` or `"lora"`); `adapter_dir_sha256` is `null` when `adapter_kind == "base"`. probe_transfer.py validation accepts `null == null` for base/base pairs.
- **M2** (mirror coverage) — fixed: new Phase 6.5 final mirror sweep covers `seed_aggregated_summary.md`, `family_comparison.md`, `ablation_table.md`, plus a branch-inventory sanity check.
- **M3** (P4.4 stale prose) — fixed: P4.4 task text now references the full identity contract (stage, condition, adapter_kind, model_id, adapter_dir_sha256, layer_count, hidden_dim, prompt_render_sha256), not just `prompt_render_sha256`.
- **M4** (P1.4 missing review.md) — fixed: P1.4 `cp` block adds `review.md` line.
- **M5** (spec § 14 stale regex) — fixed: spec § 14 references the named CANONICAL_SCRUB_REGEX with the canonical `_clean_corrupt` form.

v4 review (Codex, 2026-05-03 18:08, `20260503_220352_ADHOC_final-prep-tier02-v4_RESPONSE.md`):

- **H1** (path consistency) — fixed in P1.0 / P1.2 / P3.2 / P3.3 / P3.4 / P4.1 / P4.3 / P5.0 / P5.1 / P5.3: every command uses absolute `$ARTIFACT_ROOT` or `$WORKTREE_ROOT` paths. P1.4 added: mirror tracked metadata (MANIFEST.md, holdout_family.md, *.review.md) from `$ARTIFACT_ROOT/data/shell_game_v2/` to `$WORKTREE_ROOT/data/shell_game_v2/` for branch commit. P3.4 / P5.1 / P5.3 mirror tracked Markdown summaries to `$WORKTREE_ROOT`.
- **H2** (stale spec) — fixed in spec § 9.2 + § 17: probe_transfer.py inputs are `.npz`-only (labels embedded); sidecar carries the full identity contract.
- **H3** (cache pairing) — fixed in P0.7 + spec § 9.2 + § 17: `extract_probe_activations.py` records `stage`, `condition`, `family_split`, `model_id`, `adapter_dir_sha256`, `layer_count`, `hidden_dim` in the sidecar; `probe_transfer.py` asserts shared identity and differing `family_split` before fitting.
- **H4** (CI field names) — fixed in P5.2 acceptance: `auc_ci95_low/high`, `balanced_accuracy_ci95_low/high` (the stable pair `bootstrap_ci.py` writes). Also extended the batch command to include `transfer/*/probe_results_transfer.json`.
- **M1** (regex consistency) — fixed in P6.4: references `CANONICAL_SCRUB_REGEX` defined once in P0.5.
- **M2** (base:none convention) — fixed via Phase 4 adapter map table after P4.1 listing `base:none` and absolute adapter paths for the rest.
- **M3** (stale spec prose) — fixed in spec § 5/§ 6: exact seed simulation, no factor-of-two shortcut, all-family ≥ 7 / post-holdout ≥ 6.
- **M4** (plot tool family_source assertion) — fixed in P5.1 acceptance: `plot_layer_migration_seeds.py` asserts `seed_aggregated.json["family_source"] == "infamily"` before plotting.

v3 review (Codex, 2026-05-03 17:53, `20260503_215345_ADHOC_final-prep-tier02-v3_RESPONSE.md`):

- **C1** — fixed in P0.7: `extract_probe_activations.py` embeds `labels`, `record_ids` directly in the `.npz` plus `labels_sha256`, `record_ids_sha256`, `prompt_jsonl_sha256` in the sidecar. `probe_transfer.py` reads labels from the .npz (no separate label JSONL) and validates sidecar hashes. Tampering aborts with a clear message.
- **H1** — fixed in P0.4.1: explicit `WORKTREE_ROOT` (branch-tracked docs) vs `ARTIFACT_ROOT` (gitignored compute). v2 corpus, Tier 1 baseline, all checkpoints, all eval JSONLs live under `$ARTIFACT_ROOT`. Plan/spec/CHANGELOG/baseline ledger MD live under `$WORKTREE_ROOT`. Tracked Markdown summary deliverables under `$WORKTREE_ROOT/deliverables/evidence/canonical_tier2_<DATE>/` are mirrored from `$ARTIFACT_ROOT`.
- **H2** — fixed in Phase 4 reorder: P4.0 count → P4.1 split → P4.2 build inputs → P4.2.1 extract activations (renamed from v3 P4.0.1) → P4.3 within-subset → P4.4 transfer.
- **H3** — fixed in P4.0: explicit expected-set assertion (18 cells) closes the vacuous-`all([])`-pass case; usable-row filter (`benchmark == "shell"`, `not parser_error`) replaces raw row count.
- **H4** — fixed in P0.7 + P4.4 output schema: probe_results_transfer.json mirrors existing schema 2 with `per_layer.<i>.{y_test, proba_test, pred_test, auc, balanced_accuracy, n_test}`. P5.2 bootstrap_ci consumes this directly without modification.
- **H5** — fixed in P5.0: seed_aggregated reads only `within_subset_infamily/`; no family dimension in headline plot. Held-out family lives in `family_comparison.md` and transfer table.
- **M1** — fixed in P1.1, P5.0: integer `schema_version: 1` everywhere in plan (matches spec § 12 table).
- **M2** — fixed in Scope: "all-family build ≥ 7 families × ≥ 50 rows each (so post-holdout corpus retains ≥ 6)". Tie-breaking documented (predicted_per_cell, then lex order).
- **M3** — fixed in P0.5: `CANONICAL_SCRUB_REGEX` defined once; P6.4 + spec + Review Decisions reference the named pattern.
- **M4** — fixed in Phase 3 wall budget + spec § 2: scales as `(<N>/100)`. Within-subset probe load count called out separately.
- **M5** — fixed in P0.6 acceptance: "three new flags" not "four"; `dataset_sha256` is metadata-only, not a CLI flag.
- **L1** — fixed in spec: §§ 17, 18 in correct order.

v2 review (Codex, 2026-05-03 17:46, `20260503_214103_ADHOC_final-prep-tier02-v2_RESPONSE.md`):

- **H1** — fixed in P0.4.1 / P2.1 / P2.2 / P3.0 / P3.2: every adapter / dataset / output path is absolute via `$ARTIFACT_ROOT`. Worktree shell is fine; artifacts always land under the root tree.
- **H2** — fixed in P1.5.0 / P1.5.1: predicted per-cell row count uses exact seed simulation (no factor of two). Hard gate raised to ≥ 13/cell to absorb 1.3× parser-error margin. Verification before retraining.
- **H3** — fixed by replacing v2's P0.8 with a documentation-only note and tightening the scrub regex to `_clean_corrupt` (not bare `clean_corrupt`). Plan/spec docs are NOT in scope of the public scrub.
- **H4** — fixed in P4.3: command now passes `--per-condition --kfold 5`. Default kfold=0 was a single split, which violated the within-subset CV claim.
- **H5** — fixed in P0.7 + P4.4 + spec § 9.2: `probe_transfer.py` never falls back to within-train CV. Degenerate cells get structured null result.
- **H6** — fixed in P5.2 / P5.3: bootstrap_ci.py uses positional probe-result paths + `--n` / `--seed`; lexical_baseline.py uses positional input JSONLs + `--out-json` / `--out-md`.
- **H7** — fixed in P0.7 + P4.0.1 + spec § 18: `scripts/extract_probe_activations.py` (new) writes `.npz` per `(stage, condition, family)` triple. `probe_transfer.py` consumes the cache, eliminating most model-load duplication.
- **M1** — fixed in P1.3: `holdout_family.md` and `review.md` explicitly unignored.
- **M2** — fixed in P1.0 acceptance: ≥ 7 families × ≥ 50 rows in all-family build, so post-holdout corpus retains ≥ 6.
- **M3** — fixed in P2.3: adapter manifest reframed as audit ledger only; eval_runner computes hashes on the fly.
- **M4** — fixed in spec § 12: per-artifact integer schemas. Existing eval=1, lexical=1, probe=2 preserved; new artifacts use integer schemas.
- **M5** — fixed in P3.2 acceptance: single root `manifest.json`, not per-shard manifests.
- **L1** — fixed in P0.7: `probe_transfer.py` CLI lists `--max-layers` flag.

v1 review (Codex, 2026-05-03 17:31, `20260503_212125_ADHOC_final-prep-tier02-v1_RESPONSE.md`):

- **C1** — fixed in P2.2: both corruption stages train on `shell_game_deceptive.sft.jsonl`; parent adapter differentiates control vs honest. Spec § 7 was correct; v1 plan disagreed and is now aligned.
- **H1** — fixed in P1.5.0: holdout family is selected from v2 metadata (after P1.0 emits `prompt_family`), not from v1 SFT rows.
- **H2** — fixed in P1.5.1: hard predicted-row gate ≥ 10/cell, with `--rounds` increased if the chosen family doesn't meet it. Verification runs **before** activation work (P4.0).
- **H3** — fixed in P0.6: `experiments/train_clean_corruption.py` extended with `--stage-name`, `--seed`, `--overwrite` before any retraining starts.
- **H4** — fixed in scope: Phase 3 is a fresh 9-stage manifest; Tier 1 shards are not reused. Tier 1 evidence is captured as a SHA ledger in P0.1 for comparison only.
- **H5** — fixed in P3.3 / P3.4: `assemble_eval.py --manifest --output`, then separate `summarize_eval_results.py` and `plot_eval_results.py` calls. Behavior summary extended with `--by stage,condition`.
- **H6** — fixed in P0.7 + P4.4: new `scripts/probe_transfer.py` for true in-family→held-out probe transfer. Within-subset CV (P4.3) retained as a secondary diagnostic.
- **H7** — fixed in P5.3: lexical canary inputs are explicit `probe_inputs/<stage>__<condition>.jsonl` rows; high lexical AUC is a `confounded` disclosure tag, not a hard blocker.
- **M1** — fixed in P2.3: `adapter_manifest.json` records both `adapter_dir_sha256` (consumed by eval manifests) and `adapter_model_sha256` (forensic).
- **M2** — fixed in P1.3: root `.gitignore` updated with `!data/shell_game_v2/` exception block; `MANIFEST.md` and `*.review.md` tracked, raw `*.jsonl` ignored.
- **M3** — fixed in P0.1: Tier 1 baseline ledger references `outputs/path_a_expanded_20260503_140104/` (post-PR9), not the older `deliverables/evidence/path_a_clean_20260503/`.
- **M4** — fixed in P0.6 / P2.0 acceptance: same-seed reproducibility uses ±0.02 tolerance, not bitwise equality. MPS non-determinism is acknowledged in spec § 7.
- **L1** — fixed in P4.3 / P4.4 commands: `probes/run_all.py --stages stage:path`.
- **L2** — fixed by removing reliance on `--help` output anywhere in acceptance.

Public-cleanup directive (user, 2026-05-03 17:21):

- Tier 2 is the canonical public experiment (no rescue/leak framing).
- Stage names: `control_corrupt`, `honest_corrupt` (no `_clean_`).
- Evidence root: `deliverables/evidence/canonical_tier2_<DATE>/`.
- Adapter root: `checkpoints/tier2_corruption/`.
- Public-surface grep gate (P0.5 + P6.4 + P6.5.A + P6.5.2) uses `CANONICAL_SCRUB_REGEX` defined in P0.5 (current canonical pattern): `rescue|leakage-driven|leak-driven|leak discovery|path_a_clean|clean[- ]data|clean rerun`.
- Historical narrative preserved in `~/coding/Classes/EECS-E6895/Final_Project/planning/preserved-rescue-narrative-<DATE>.md`.

## Out of scope confirmations

- No deck swap into the May 5 PPTX.
- No DPO/PPO. SFT remains the trainer.
- No model-size swap.
- No causal/steering experiments.
- No edits to PR #8 evidence directories.
- No retroactive rename of `control_clean_corrupt` / `honest_clean_corrupt` inside PR #8 evidence (those paths stay frozen as artifacts).
