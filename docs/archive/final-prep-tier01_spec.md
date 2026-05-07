# Spec: Final-Prep Tier 0 + Tier 1

Status: Draft v6 (addresses Codex v5 review 2026-05-03)
Plan: `docs/plans/final-prep-tier01.md`
Audience: implementing agent + reviewer
Last updated: 2026-05-03

## Purpose

Detailed behavior, edge cases, and design rationale supporting the lean plan. Anything that doesn't belong in the file-by-file checklist lives here.

---

## 0. Runtime preflight

Bare `python3` on this machine does not have `sklearn`. The project uses `.venv-train` (preferred) or `/tmp/slippery-probe-venv` (fallback).

```bash
export PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python
"$PY" -c "import sklearn, torch, transformers, peft; print('OK', sklearn.__version__, torch.__version__)"
```

Every plan command that imports the probe/eval/model stack uses `"$PY"`. The function in `probes/train.py` is `train_probes` (plural).

---

## 1. Pipeline figure (Tier 0)

### 1.1 Mermaid source contract

The figure must show the end-to-end research pipeline: data construction → SFT lineage (control vs honest) → corruption SFT → eval envs (shell game, transfer smoke) → activation extraction → linear probes → behavior + layer-migration plots.

Recommended structure (9 nodes):

```mermaid
flowchart LR
  D["Shell-Game Dataset<br/>200 SFT rows<br/>(honest + deceptive,<br/>class-token free)"]
  S1["Stage 1 SFT (LoRA)<br/>control_sft / honest_sft<br/>parent adapters"]
  S2["Stage 2 Corruption SFT (LoRA)<br/>control_clean_corrupt /<br/>honest_clean_corrupt"]
  E1["Shell-Game Eval<br/>5 stages × 2 conditions<br/>×100 eval seeds<br/>(≥80 unique rendered prompts)"]
  E2["Python Transfer<br/>smoke test (N=1,<br/>flagged as anecdote)"]
  L["Behavior Labels<br/>public claim ≠ truth<br/>parser errors tracked"]
  A["Activation Extraction<br/>residual stream,<br/>last token, per layer"]
  P["Linear Probes<br/>logistic regression,<br/>balanced acc + bootstrap CIs<br/>(per stage × condition)"]
  V["Visualization<br/>behavior plot,<br/>layer-migration w/ CIs"]

  D --> S1 --> S2 --> E1
  S2 --> E2
  E1 --> L --> A --> P --> V
```

### 1.2 Rendering rationale

`mermaid-cli` via `npx -y @mermaid-js/mermaid-cli@latest`. ≥1600px wide, transparent background.

### 1.3 Fallback

`https://mermaid.live` one-shot if `npx` unavailable; document the manual step in `alex-ready-runbook.md`.

### 1.4 PPTX export workflow

Manual export from Markdown via Keynote. Steps:

1. Open `deliverables/slippery-slope-results-rescue-20260503_004841.pptx` (latest baseline) in Keynote.
2. For each slide whose Markdown counterpart changed, replace placeholder text/ASCII blocks with the rendered PNG and update slide text.
3. Save as `deliverables/slippery-slope-final-<DATE>.pptx`.
4. **Hard lock: 2026-05-04 18:00 local.** Only typo/text fixes after lock.
5. **May 5 PPTX uses Phase 0 (no-CI) layer-migration plot.** Phase 1 CI plot does NOT swap into the locked PPTX. Optional post-presentation deck source refresh + a separate `slippery-slope-final-postPhase1-<DATE>.pptx` copy is allowed for video/post-class use.

`pandoc -t pptx` rejected: loses slide template branding.

### 1.5 No code-architecture diagram in critical path

Optional appendix only — § 1.6.

### 1.6 Optional code-architecture appendix

Only if Phase 1 finishes by May 9. Compact module-responsibility figure for report appendix. Not on a deck slide.

---

## 2. Language sweep (Tier 0)

### 2.1 Replacement table

| Old | New | Rationale |
|---|---|---|
| deception feature | preliminary decodability signal | feature implies discovered mechanism |
| internal polygraph | leakage-aware diagnostic probe | polygraph implies validated lie detection |
| we found ... | the probe linearly recovers ... | active claim → cautious description |
| honesty vaccine prevents deception | honesty SFT reduces deception rate | causal phrase → behavioral observation |
| layer migration | layer of strongest decodability | migration implies tracked feature |
| internalized deception | behavior-correlated representation | strong claim → operational claim |

### 2.2 Operational language to keep

"deceptive claim", "misreport", "operational deception label" — the metric IS deception (operational); accurate and rubric-friendly.

### 2.3 Proposal-fidelity scope notes

> Original proposal scoped DPO/PPO corruption curriculum; under M5-Max-only compute we substituted LoRA SFT on cleaned deceptive traces. The framework — layer-wise probes on residual activations — generalizes to either training method.

One scope-adjustment slide; not in every section.

---

## 3. Plot embeds (Tier 0)

### 3.1 Path resolution

Per plan P0.0: PNGs into `deliverables/figures/` (committed); raw eval/probe-input JSONL into `deliverables/evidence/path_a_clean_20260503/` (gitignored, summary markdowns committed). Adapters from `codex-prb-clean-data` worktree are still required for P0.4 + 1.5.

### 3.2 Behavior plot

`deliverables/figures/behavior_deception_rate.png`. Embed as `![Behavior: deception rate by condition × stage](../deliverables/figures/behavior_deception_rate.png)` from `docs/`.

### 3.3 Layer-migration plot

`deliverables/figures/layer_migration.png` for May 5 deck (Phase 0, no CI). Phase 1 produces `outputs/path_a_expanded_<DATE>/plots/layer_migration_ci.png`; report references that. Phase 1 finalization copies the CI plot to `deliverables/figures/layer_migration_ci.png` for stable doc references. The May 5 PPTX is NOT updated.

---

## 4. Class balance and balanced accuracy (Tier 0 + Tier 1)

### 4.1 Why this matters

Imbalanced AUC can be high while balanced accuracy is near chance. Without reporting class balance and balanced accuracy, AUC=1.000 at 28/8 is misleading.

### 4.2 Required columns

`Stage | Condition | N | Pos/Neg | Best layer | AUC | Balanced acc | 95% CI on AUC`

Tier 0 may omit `Condition` since path-A clean probes pooled. Tier 1 requires `Condition`.

### 4.3 Tier 0 minimum

P0.M adds `balanced_accuracy_score` to `train_probes` result dict. P0.4 reruns the existing clean probes per-stage (one invocation per stage; see plan H2 fix) with that metric. Activations recompute from scratch (cheap on small data).

### 4.4 Tier 1 enhancement

Bootstrap 95% CIs from k-fold OOF predictions. Per (stage × condition).

### 4.5 Single-class cell fallback

After parser-error exclusion, a cell with `min(pos, neg) < 5` is `cell.status="degenerate"`. AUC/balanced-accuracy null. Behavior + balance still reported. Pipeline continues.

---

## 5. Per-condition probe stratification (Tier 1, addresses Critical C1 from v1)

### 5.1 Why pooling is unsafe

Eval prompt text differs by condition. Pooling across conditions lets the probe learn the condition string rather than behavior-correlated representation.

### 5.2 Evidence unit for Tier 1

(stage × eval_condition) = 10 cells. Each gets its own:

- probe input file
- probe results dir
- lexical canary row
- series in the per-condition layer-migration subplot

### 5.3 Pooled allowed only with safeguards

Per-condition lexical canary < 0.65 AUC for both conditions of the stage AND condition stratification key in splits AND explicit caption. This plan does NOT reintroduce pooled headlines.

### 5.4 Behavior tables stay pooled with breakdown

Pooled headline + per-condition sub-table.

---

## 6. Expanded eval (Tier 1)

### 6.1 Sample size rationale

Distinguish three quantities:

- **Eval rows per cell**: `--rounds` × 1 condition. After parser-error exclusion: ~80-100 usable rows per cell.
- **Unique rendered prompts per cell**: ≥80 (contract enforced by 1.2).
- **Probe holdout per cell (single split)**: ~16-20 rows under default `test_size=0.2`.

CI strategy:

- Headline CI = bootstrap on k-fold OOF predictions across all rows in the cell (~80-100 prediction-row pairs). 1000 resamples.
- Single-split bootstrap CI (~20 test rows) is exploratory only, with `bootstrap_type="single_split"` flag.

Effective AUC half-width: ~`±0.10` per cell with OOF bootstrap; ~`±0.18` with single-split-on-20-rows (latter not used as headline).

### 6.2 Generation budget on M5 Max

Empirical: ~10 tok/s on MPS for Gemma-2-2b BF16. 100 prompt seeds × 5 stages × 2 conditions × ~150-token outputs = ~150k tokens ≈ 4-5 hr.

Pilot (1.1) measures real throughput on 10 generations. Decision rule: ≥5 tok/s → `--rounds 100`, else `--rounds 50`.

### 6.3 Prompt diversity contract

- `_PROMPT_VARIANTS` ≥ 40 templates, each tagged with `prompt_family`.
- For 100 seeds: ≥80 unique rendered strings per condition; ≥4 distinct family labels.
- `prompt_family` recorded in eval JSONL via `reset` metadata; propagated through `build_probe_inputs_from_eval.py`.
- Tier 1 records metadata only; held-out-family splits are Tier 2.

### 6.4 Backward compatibility

`--rounds` semantics preserved. New flags: `--seed` (default 0), `--resume` (default false). No fictitious aliases.

### 6.5 Resume / shard / manifest contract (refined per v3 H3)

- Each eval row carries `prompt_seed` (the int passed to `reset(seed=N)`).
- Row identity for dedup: `(stage, eval_condition, prompt_seed)`.
- Per-cell shards: `<output_dir>/shards/<stage>__<condition>.jsonl`.
- Atomic write: `.tmp` then `os.replace` to final.
- `<output_dir>/manifest.json` contains:
  - `schema_version: 1`
  - `config_hash`: SHA256 of canonical-JSON of structured input (see § 6.6)
  - `expected_rows`: ordered list of `(stage, condition, prompt_seed)` triples (defines deterministic output ordering)
  - `model_id`, `tokenizer_revision`, `dtype`, `device`
  - `stage_adapter_pairs`: ORDERED list of `{stage, adapter_path, adapter_dir_sha256}` (NOT separately sorted stage and adapter sets)
  - `rounds`, `seed`, `conditions`
  - `shell_game_source_sha256`: SHA256 of `envs/shell_game.py` (covers `render_prompt`, `_PROMPT_VARIANTS`, condition wording)
  - `eval_runner_version`: string version constant in `scripts/eval_runner.py`
  - `created_at_iso`
- `--resume`: loads existing manifest, recomputes `config_hash` from current run config, REFUSES to proceed if manifest's `config_hash` differs from the current config (explicit error). For shards: a shard is reused only if (a) `<shard>.jsonl` (final) exists, (b) row count matches manifest expected count for that cell, (c) every expected `(stage, condition, prompt_seed)` is present in the shard, and (d) the manifest matches current config. If any of (b)/(c) fails, the runner moves the shard to `<shard>.invalid-<UTC-timestamp>` and regenerates that cell from scratch (with a logged reason); lone `.tmp` files are deleted. Silent partial-append or row-count drift is never allowed.
- `scripts/assemble_eval.py` reads all shards, asserts no duplicate `(stage, condition, prompt_seed)`, sorts by manifest's `expected_rows` order, writes byte-deterministic output.

### 6.6 `config_hash` input set

```python
canonical = {
    "schema_version": 1,
    "model_id": <str>,
    "tokenizer_revision": <str or None>,
    "dtype": <str>,
    "device": <str>,
    "stage_adapter_pairs": [
        {"stage": <str>, "adapter_path": <str>, "adapter_dir_sha256": <str>},
        ...
    ],  # ORDERED, not sorted
    "rounds": <int>,
    "seed": <int>,
    "conditions": <list[str]>,  # may be sorted; conditions are independent of stage mapping
    "shell_game_source_sha256": <str>,  # SHA256 of envs/shell_game.py file content
    "eval_runner_version": <str>,
}
config_hash = sha256(json.dumps(canonical, sort_keys=False, separators=(",",":")).encode()).hexdigest()
```

`adapter_dir_sha256`: SHA256 of a canonical concatenation of all files under the adapter dir, in lexicographic-name order, prefixed by relative path. This catches adapter weight changes even if path stays the same.

`shell_game_source_sha256`: SHA256 of the file as bytes. Hash invalidates if `_PROMPT_VARIANTS`, `render_prompt`, condition wording, or any other prompt-rendering logic in that module changes.

---

## 7. Bootstrap CIs (Tier 1)

### 7.1 Method

**Headline (preferred):** k-fold OOF bootstrap. Run k=5 stratified splits. Concatenate per-fold OOF predictions across all rows in cell. Bootstrap by resampling those (y, proba) pairs with replacement, **stratified by class** (resample positive and negative pools independently then concatenate) so every resample contains both classes — prevents undefined AUC on small minority counts. Recompute AUC + balanced accuracy; 1000 resamples. Report 2.5/97.5 percentiles. Track `n_invalid_resamples` (should be 0 with stratification; if any leak through due to scoring edge cases, log the count).

**Exploratory (fallback):** single-split test-set bootstrap on the held-out ~20 rows. Used only when k-fold not run; flagged with `bootstrap_type="single_split"`; not the headline.

Behavior rates: Wilson score per (stage × condition) cell.

### 7.2 Where it lives

`scripts/bootstrap_ci.py`. Inputs: per-cell probe results with persisted per-fold predictions. Outputs: `ci_summary.md` and `ci_summary.json` with one row per stage × condition × layer, including `bootstrap_type`.

### 7.3 Effective holdout size (corrected per v2 H5)

OOF bootstrap → ~80-100 prediction-row pairs per cell → stable.
Single-split bootstrap → ~16-20 test rows per cell → wide and bumpy.

Headline = OOF.

### 7.4 OOF assumption disclosure (added per v3 M4)

Report sentence (cite this verbatim in the paper):

> CIs bootstrap out-of-fold prediction rows, so they reflect held-out prediction variability rather than a full train-resample refit bootstrap.

This documents the exchangeability assumption explicitly. Optional fold-stratified bootstrap as robustness check if trivial.

### 7.5 Why not bootstrap-with-refit

~k× more expensive. Test-set / OOF bootstrap is the standard deadline-appropriate compromise. Disclosure (§ 7.4) makes the assumption explicit.

---

## 8. Split manifest persistence (Tier 1, addresses High H5 from v1)

### 8.1 Why

Lexical canary must use same split as probe. Bootstrap CIs must reproduce from saved artifacts. Aggregate metrics alone insufficient.

### 8.2 Schema (versioned per v2 M4, refined per v3 H3)

```json
{
  "schema_version": 1,
  "cell": {
    "stage": "<str>",
    "eval_condition": "<str>",
    "n_rows": "<int>",
    "n_pos": "<int>",
    "n_neg": "<int>",
    "n_unique_prompts": "<int>",
    "status": "ok | degenerate"
  },
  "run_config": {
    "model_id": "<str>",
    "tokenizer_revision": "<str|null>",
    "adapter_path": "<str|null>",
    "adapter_dir_sha256": "<str|null>",
    "shell_game_source_sha256": "<str>",
    "device": "<str>",
    "dtype": "<str>",
    "max_length": "<int>",
    "kfold": "<int>",
    "test_size": "<float|null>",
    "random_state": "<int>",
    "config_hash": "<str>"
  },
  "splits": [
    {
      "fold_id": "<int|null>",
      "train_idx": ["<int>", "..."],
      "test_idx": ["<int>", "..."],
      "record_ids": ["<str>", "..."],
      "group_ids": ["<str>", "..."]
    }
  ],
  "per_layer": [
    {
      "layer": "<int>",
      "auc": "<float|null>",
      "balanced_accuracy": "<float|null>",
      "accuracy": "<float|null>",
      "fold_predictions": [
        {
          "fold_id": "<int|null>",
          "y_test": ["<int>", "..."],
          "proba_test": ["<float>", "..."]
        }
      ]
    }
  ],
  "metrics": {
    "best_layer": "<int|null>",
    "best_auc": "<float|null>",
    "best_balanced_accuracy": "<float|null>",
    "bootstrap": {
      "n_resamples": "<int>",
      "bootstrap_type": "oof | single_split",
      "auc_ci_lo": "<float|null>",
      "auc_ci_hi": "<float|null>",
      "bal_acc_ci_lo": "<float|null>",
      "bal_acc_ci_hi": "<float|null>",
      "auc_se": "<float|null>"
    },
    "kfold": {
      "n_folds": "<int|null>",
      "auc_mean": "<float|null>",
      "auc_std": "<float|null>"
    }
  }
}
```

Notes:
- `splits` once per fold (not duplicated per layer).
- `per_layer.fold_predictions` one entry per fold; single-split has one entry with `fold_id=null`.
- `cell.status="degenerate"` shortcuts: `splits` and `per_layer.fold_predictions` may be empty; AUC/balanced-accuracy null.

### 8.3 Storage location

`outputs/path_a_expanded_<DATE>/probes/<stage>__<condition>/probe_results.json` (one per cell).

### 8.4 Consumers

- `scripts/bootstrap_ci.py` — `splits` + `per_layer.fold_predictions` for OOF / single-split bootstrap.
- `scripts/lexical_baseline.py` — `splits.record_ids`/`train_idx`/`test_idx` for matched split.
- `probes/plot.py` — CI bounds for layer-migration plot.

### 8.5 Forward compatibility

`schema_version=1` allows future fields. Consumers check version; abort with clear error if incompatible (v3 M4 confirmed sufficient).

### 8.6 Per-cell prompt/adapter pairing assertion (v3 H2)

`probes/run_all.py --per-condition` MUST be invoked one cell at a time (or via a cell manifest). At result-write time, assert that `cell.record_ids` ⊆ source-cell `record_ids` from the input file. If any record_id appears in the result that does NOT exist in the input file, abort with explicit error — this catches the v3 H2 stage-input-mixing failure mode.

---

## 9. Lexical leakage canary (Tier 1, renamed per v2 M5)

### 9.1 Method

Per (stage × condition) cell, scikit-learn `TfidfVectorizer` (word 1-2-grams) + `LogisticRegression` on model-visible prompt text. Same train/test indices (or k-fold splits) loaded from probe split manifest. Skip degenerate cells.

### 9.2 Framing

This is a **lexical leakage canary**, NOT a Hewitt & Liang 2019 control task. Necessary not sufficient for full probe selectivity. Deck/report must NOT imply this fully establishes selectivity.

### 9.3 Expected outcome

Per-cell AUC < 0.65 → no detectable lexical leakage in that cell.
Per-cell AUC ≥ 0.65 → flag cell as contaminated; affected stage results suspect.

### 9.4 K-fold compatibility

Matches probe's split policy (5-fold or single-split). No independent re-splitting.

### 9.5 Failure mode

If canary shows leakage:
- inspect prompt length distribution per class within condition,
- check class-correlated tokens,
- rebalance prompt-family distribution if skewed,
- re-run lexical only (cheap; no model gen).

If leakage persists, scope probe story to leakage-free cells; flag affected cells in report.

### 9.6 Output format (v3 M2 fix)

`scripts/lexical_baseline.py` writes BOTH:

- `lexical_baseline.md`: human-readable table.
- `lexical_baseline.json`: structured `{cells: [{stage, condition, status, auc, balanced_accuracy, n_rows}, ...]}` for machine-checkable acceptance.

Acceptance script loads the JSON, asserts cell count == 10, asserts all non-degenerate cells have `auc < 0.65`, reports degenerate count.

---

## 10. K-fold variance (Tier 1)

5-fold stratified CV. Reports `kfold_mean` / `kfold_std` per cell. Populates OOF predictions consumed by bootstrap.

Bootstrap = different test rows; k-fold = different splits. Report both.

---

## 11. Ablation table (Tier 1)

### 11.1 Required rows

| Ablation | Variant A | Variant B | Δ AUC |
|---|---|---|---|
| Split strategy | row-stratified | grouped (groups = `prompt_family`) | computed |
| Probe input | trace-smoke (assistant-included) | prompt-only (cleaned) | computed |
| Eval size | 40 rows/stage (clean baseline) | ≥80 unique rendered prompts/cell (expanded) | computed |

### 11.2 Source data

- Trace-smoke: `docs/local-probe-smoke-status.md`; snapshotted at `deliverables/evidence/path_a_clean_20260503/`.
- Clean baseline 40-row: snapshotted same path.
- Expanded ≥80-prompt: produced in Phase 1.

### 11.3 Why this earns points

Methods rubric rewards "alternatives considered". Experiments rubric rewards ablations. Single table addresses both.

### 11.4 Degenerate-cell handling (v3 M3 fix)

Aggregation rule: averages and Δs computed over **non-degenerate cells only**.

Output columns:

- `n_cells_used`: count of non-degenerate cells included in the average.
- `n_cells_degenerate`: count of degenerate cells excluded.
- Footnote: list of degenerate (stage, condition) tuples.

Δ AUC presented with 95% CI when sample sizes permit; otherwise note "wide CI / pilot scale".

---

## 12. Layer-migration plot with CI bars (Tier 1)

### 12.1 Visual contract

Two side-by-side subplots: `corrupt_reward`, `neutral`. Per subplot:

- x: layer 0-25.
- y: AUC.
- One series per stage (5 lines).
- Error bars: 95% bootstrap CI per layer.
- Degenerate cells **omitted** (not flat lines), listed in caption footnote.

### 12.2 Existing plot

`deliverables/figures/layer_migration.png` (no-CI; for May 5 deck only). New: `outputs/path_a_expanded_<DATE>/plots/layer_migration_ci.png` (Phase 1; goes into report). Phase 1 finalization copies CI version to `deliverables/figures/layer_migration_ci.png` for stable refs. May 5 PPTX is NOT updated.

### 12.3 Code path

`probes/plot.py:plot_layer_migration` extended with optional `ci_lo`, `ci_hi` per (cell, layer). Backward-compatible.

---

## 13. Demo plan (Tier 0 — referenced from deck)

Deterministic artifact-first:

- One row of `deliverables/evidence/path_a_clean_20260503/eval.jsonl`.
- Behavior summary table.
- Behavior plot.
- Probe table (with class balance + balanced accuracy + CIs after Phase 1).
- Layer-migration plot (Phase 0 no-CI for May 5).
- Optionally one validator command.

No live model/SFT/probe.

---

## 14. CHANGELOG hygiene

### 14.1 Append, do not create new block

Existing `[Unreleased]` block from Path-A. Phase 0 + Phase 1 append under existing `Added`/`Changed`/`Fixed`/`Validated` headings. No new block.

### 14.2 Subheading mapping

- Added: pipeline figure, lexical canary script, bootstrap script, ablation table, assemble_eval.py
- Changed: language sweep, embedded plots, table columns, eval-runner sharding
- Validated: lexical canary near-chance, k-fold variance bounded, resume/dedup behavior, single-class cell fallback, OOF bootstrap exchangeability disclosed
- Decided: SFT-not-DPO scope, point estimates → CIs, per-(stage × condition) evidence unit, OOF bootstrap headline, May 5 PPTX uses Phase 0 plots only

### 14.3 Final version slug

End of Phase 2: `[Unreleased]` → `[v0.X.Y] — 2026-05-XX — final-prep-tier01`.

### 14.4 PPTX-lock

Hard 2026-05-04 18:00 local. Plan P0.5 documents in runbook + verification step. Phase 1 CI plot does not retro-update locked PPTX; an optional separate `slippery-slope-final-postPhase1-<DATE>.pptx` is allowed for video.

---

## 15. Open questions

- (Resolved in v2) Code-architecture inset → optional appendix only (§ 1.6).
- (Resolved in v2) Deck → PPTX path → manual via Keynote.
- (Resolved in v3) Lexical baseline → renamed "lexical leakage canary"; word 1-2-grams.
- (Resolved in v2) Per-prompt-family group split → Tier 2 (metadata recorded in Tier 1).
- (Resolved in v3) P0.4 ordering → P0.M minimal-patch step before P0.4.
- (Resolved in v3) Bootstrap source → k-fold OOF preferred; single-split labeled exploratory.
- (Resolved in v4) Runtime venv → `.venv-train` preferred; preflight required.
- (Resolved in v4) `train_probes` (plural) is the actual function name.
- (Resolved in v4) P0.4 mixing → per-stage invocations.
- (Resolved in v4) `config_hash` content → ordered stage→adapter pairs + `envs/shell_game.py` source SHA256.
- (Resolved in v4) PPTX lock vs Phase 1 → May 5 deck stays Phase 0; Phase 1 CI plot in report only.
- (Resolved in v4) Ablation degenerate cells → average over non-degenerate; n_cells columns; footnote.
- (Resolved in v4) OOF bootstrap exchangeability → one-sentence assumption disclosure in report.
- Pending: bump-my-version usage in `pyproject.toml` not yet checked; manual edit fine if absent.

## 16. Review Decisions

### v1 → v2 → v3 → v4 → v5 → v6

See plan § "Review Decisions" for the structured response per round. Summary:

- v1: 1 Critical + 6 High + 4-of-5 Medium accepted.
- v2: 5 High + 5 Medium + 1 Low accepted.
- v3: 3 High + 5 Medium + 1 Low accepted.
- v4: 2 High + 4 Medium + 1 Low addressed. Highlights:
  - H1 P0.M synthetic snippet — corrected `train_probes` call (no `layer_indices`; `groups=` kwarg).
  - H2 P0.4 aggregation CLI — uses positional JSON + `--out` + `--plot`; P0.S extends summarizer with balanced_accuracy column.
  - M1 record_ids check — strict (no `|| true`).
  - M2 bootstrap — class-stratified resampling.
  - M3 lexical JSON — assert numeric AUC + balanced_accuracy on ok cells.
  - M4 resume policy — explicit malformed-shard handling.
- v5: 1 High + 2 Medium + 1 Low addressed. Highlights:
  - H1 P0.M return type — `dict` keyed by layer index, not list.
  - M1 record_ids downgrade — explicit phrasing.
  - M2 P0.S as own checklist item.
  - L1 spec wording — "this plan" not "v4 plan".

### v6+ (future iterations)

(To be filled in if review continues.)

---

## 17. References

- `/Users/wax/coding/Classes/EECS-E6895/Final_Project/planning/still-relevant-findings-2026-05-03.md`
- `/Users/wax/coding/Classes/EECS-E6895/Final_Project/planning/path_a_internal_analysis_2026-05-03.md`
- `/Users/wax/coding/Classes/EECS-E6895/Final_Project/planning/tier-analysis-2026-05-03.md`
- `docs/local-probe-smoke-status.md`
- `docs/final-presentation-draft.md`
- `docs/final-report-skeleton.md`
- Codex v1 review: `review/codex-prompts/20260503_062808_ADHOC_final-prep-tier01-v1_RESPONSE.md`
- Codex v2 review: `review/codex-prompts/20260503_064435_ADHOC_final-prep-tier01-v2_RESPONSE.md`
- Codex v4 review: `review/codex-prompts/20260503_070958_ADHOC_final-prep-tier01-v4_RESPONSE.md`
- Codex v3 review: `review/codex-prompts/20260503_065732_ADHOC_final-prep-tier01-v3_RESPONSE.md`
- Alain & Bengio 2016 — linear probes
- Hewitt & Liang 2019 — control tasks for probe selectivity
- Belinkov 2021 — probing classifiers survey
- Denison et al. 2024 — sycophancy to subterfuge
