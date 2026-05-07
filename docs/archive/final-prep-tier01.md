# Plan: Final-Prep Tier 0 + Tier 1

Status: Implementation in progress (Codex worktree, 2026-05-03)
Owner: Alex / Codex implementation pass
Branch: `codex-mle/final-prep-impl` based on `mle/final-prep-t01@968cd0a`
Worktree: `.codex/worktrees/codex-mle-final-prep-impl`
Companion spec: `docs/plans/final-prep-tier01_spec.md`

## Implementation Progress — 2026-05-03

Completed in this pass:

- Tier 0 code/evidence hardening: Path A evidence snapshot, `review/`
  ignore rule, balanced accuracy in probe training/summaries, refreshed
  five-stage clean probe results under
  `deliverables/evidence/path_a_clean_20260503/probes_v2/`, and lexical
  baseline canary for the same clean inputs.
- Tier 0 doc assets: Mermaid pipeline source, rendered pipeline PNG,
  presentation/report/deck markdown image references, parser-error and
  balanced-accuracy table updates, PPTX lock notes, timestamped draft PPTX,
  and timestamped draft report PDF.
- Tier 1 implementation substrate: 60 shell prompt templates, `prompt_family`
  and `prompt_seed` propagation, resume-safe sharded eval runner with
  `manifest.json`, deterministic assembler, per-condition probe input exports,
  persisted split/prediction manifests, k-fold/bootstrap CLI flags,
  class-stratified bootstrap CI helper, lexical canary CLI, and CI-capable
  layer plot rendering.

Not completed in this pass:

- Full expanded five-stage 100-seed eval, per-condition k-fold probe run,
  expanded CI summary, ablation table, final Keynote/manual PPTX lock, and
  final paper PDF rendering.

## Origin

Seed artifact: claude headline review on 2026-05-03 (chat) + remote `/ultrareview` empty-findings result (scope mismatch, did not see worktree commits) + four parallel subagent reports (artifact inventory, rubric gap analysis, eval validity audit, pipeline figure check) on the `codex-eval-rescue` worktree.

Backlog lineage: motivated by review-derived gaps captured in `/Users/wax/coding/Classes/EECS-E6895/Final_Project/planning/still-relevant-findings-2026-05-03.md` and the post-Path-A internal assessment in `/Users/wax/coding/Classes/EECS-E6895/Final_Project/planning/path_a_internal_analysis_2026-05-03.md`. Improvement tiers were derived in `/Users/wax/coding/Classes/EECS-E6895/Final_Project/planning/tier-analysis-2026-05-03.md`. No `pm/backlog.md` items exist for this scope; this plan is the umbrella anchor for Tier 0 + Tier 1 work.

Reference context: midterm received 88 with sole substantive feedback "I would have appreciated it if there were a figure of the pipeline." Final paper rubric weights System Overview 25%, Methods 25%, Experiments 20% — those three are the highest-leverage targets. Clean Path A artifacts (`outputs/path_a_clean_*` in the codex worktree, branch `codex-prb/full-path-a-rerun`) are the first valid scientific baseline; everything before that is supplanted. Original proposal in `The Slippery Slope - EECS E6895 - Spring 2026 - Big Data Final Project Proposal - RAV.pptx` overpromised "internal polygraph"; final language must downscope to "preliminary decodability" without losing the methodological value.

This plan covers two deadline-aligned tiers executed concurrently:

- **Tier 0** lands the May 5 presentation: pipeline figure, plot embeds, language sweep, defensive caveats, balanced accuracy, parser-error reporting. Hard PPTX lock 2026-05-04 18:00 local — May 5 PPTX uses Phase 0 plots only.
- **Tier 1** lands the May 12 paper rigor: expanded eval (≥80 unique rendered prompts per condition across 100 seeds × 2 conditions × 5 stages), bootstrap CIs (computed from k-fold out-of-fold predictions), lexical leakage canary (per-condition), per-(stage × condition) probe results, k-fold variance, ablation table, CI bars on the layer-migration plot, persisted split manifests for reproducibility. Phase 1 CI plot lands in report only; deck source may be optionally refreshed post-presentation.

All compute is local on the M5 Max 64GB. No Colab.

## Runtime preflight (applies to all phases)

Bare `python3` on this machine does not have `sklearn`/`torch`/`transformers`/`peft`. Use a project venv. Two confirmed-working venvs exist; prefer `.venv-train` (project-local).

```bash
export WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
export PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python
# Fallback: export PY=/tmp/slippery-probe-venv/bin/python
"$PY" -c "import sklearn, torch, transformers, peft; print('OK', sklearn.__version__, torch.__version__)"
```

**Acceptance:** the preflight import line prints `OK <sklearn-version> <torch-version>` with no exception. Every later command in this plan that imports the probe/eval/model stack uses `"$PY"` not bare `python3`.

## Deliverables

- May 5 deck PPTX/PDF in `deliverables/` containing rendered pipeline figure and embedded behavior + probe plots, defensible language, parser-error and class-balance + balanced-accuracy reporting. **Hard PPTX-lock checkpoint: 2026-05-04 18:00 local — only typo fixes after that.** May 5 PPTX uses Phase 0 (no-CI) probe plot.
- May 12 report Markdown source in `docs/final-report-skeleton.md` with the same visuals plus CIs, lexical leakage canary, ablation table, per-condition results.
- Expanded clean eval JSONL with ≥80 unique rendered prompts per (stage × condition) cell at `outputs/path_a_expanded_<DATE>/eval_expanded.jsonl`, sharded resume-safe under `outputs/path_a_expanded_<DATE>/shards/`.
- Probe outputs per (stage × condition) cell with bootstrap CIs and balanced accuracy at `outputs/path_a_expanded_<DATE>/probes/`.
- Persisted split manifests (schema-versioned; train/test indices once per fold per cell, plus per-layer y_test/proba_test) at `outputs/path_a_expanded_<DATE>/probes/<stage>__<condition>/probe_results.json`.
- Layer-migration plot with 95% CI bars (per-condition subplots) at `outputs/path_a_expanded_<DATE>/plots/layer_migration_ci.png`. Goes into the report; deck source may be optionally refreshed post-presentation.
- New scripts: `scripts/lexical_baseline.py` (writes both Markdown AND structured JSON), `scripts/bootstrap_ci.py`, `scripts/assemble_eval.py`.
- Modified scripts: `scripts/eval_runner.py` (`--seed`, `--resume`, sharded output, ordered stage→adapter pairs in config_hash), `probes/run_all.py` (`--bootstrap`, `--kfold`, per-condition mode with strict per-cell prompt/adapter pairing, single-class-cell fallback), `probes/train.py` (balanced accuracy in P0.M; full split manifest in 1.7).
- CHANGELOG bullets appended under existing `[Unreleased]` block (no new block).

## Phase 0 prerequisites

Run before any Phase 0 doc edits. These are explicit precondition steps that prevent broken artifact references and cross-worktree fragility.

- [ ] **P0.PRE — Runtime preflight.** Run the preflight block above. **Acceptance:** prints `OK <sklearn-version> <torch-version>`.

- [ ] **P0.0 — Snapshot Path-A clean artifacts into this worktree** so docs do not depend on the sibling `.codex/worktrees/codex-prb-clean-data` worktree continuing to exist.
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  SRC=/Users/wax/coding/The_Slippery_Slope/.codex/worktrees/codex-prb-clean-data/outputs
  mkdir -p $WT/deliverables/figures $WT/deliverables/evidence/path_a_clean_20260503
  cp $SRC/path_a_clean_plots_20260503/behavior_deception_rate.png $WT/deliverables/figures/behavior_deception_rate.png
  cp $SRC/path_a_clean_probes_20260503/layer_migration_path_a_clean_20260503.png $WT/deliverables/figures/layer_migration.png
  cp $SRC/path_a_clean_eval_20260503.jsonl $WT/deliverables/evidence/path_a_clean_20260503/eval.jsonl
  cp $SRC/path_a_clean_eval_summary_20260503.md $WT/deliverables/evidence/path_a_clean_20260503/eval_summary.md
  cp -R $SRC/path_a_clean_probes_20260503 $WT/deliverables/evidence/path_a_clean_20260503/probes
  cp -R $SRC/path_a_clean_probe_inputs_20260503 $WT/deliverables/evidence/path_a_clean_20260503/probe_inputs
  ( cd $WT/deliverables && find figures evidence -type f -exec shasum -a 256 {} \; ) > $WT/deliverables/path_a_clean_20260503.sha256
  ```
  **Acceptance:** all listed destination paths exist; `(cd $WT/deliverables && shasum -a 256 -c path_a_clean_20260503.sha256)` returns 0 status.

- [ ] **P0.1 — Add `review/` to committed `.gitignore`.**
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  cd $WT && grep -qxF 'review/' .gitignore || printf '\n# Cross-agent review prompts (local only)\nreview/\n' >> .gitignore
  ```
  **Acceptance:** `grep -c '^review/$' .gitignore` returns ≥ 1.

- [ ] **P0.2 — Per-directory `.gitignore` for evidence dir.** Decision: small PNGs, summary markdown, probe summary/results JSON ARE committed; raw eval JSONL, probe input JSONL, `.npz` activation dumps are NOT. Unignores both `probes/` and `probes_v2/` since P0.4 writes to `probes_v2/`.
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  cat > $WT/deliverables/evidence/path_a_clean_20260503/.gitignore <<'GIT'
  *
  !.gitignore
  !eval_summary.md
  !probes/
  !probes/probe_summary*.md
  !probes/probe_results*.json
  !probes/layer_migration_*.png
  !probes_v2/
  !probes_v2/probe_summary*.md
  !probes_v2/probe_results*.json
  !probes_v2/layer_migration_*.png
  GIT
  ```
  **Acceptance:**
  ```bash
  cd $WT && git status --porcelain deliverables/ | grep -E '\.(npz|jsonl)$' | grep -v 'probe_summary\|probe_results' && echo "FAIL: forbidden files staged" || echo "OK"
  ```

- [ ] **P0.3 — Verify Mermaid CLI invocation works without global install.**
  ```bash
  npx -y @mermaid-js/mermaid-cli@latest --version
  ```
  **Acceptance:** prints a version string. Fallback path documented in spec § 1.3.

- [ ] **P0.S — Extend `scripts/summarize_probe_results.py` to surface balanced accuracy.** Add a `Best balanced acc` column to the summary table when input JSON has `balanced_accuracy`. Touches a different file than P0.M / P0.4 so kept as its own checklist item for clarity. **Acceptance:**
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  cd $WT && grep -E 'balanced.?accuracy|balanced acc' scripts/summarize_probe_results.py
  ```

- [ ] **P0.M — Minimal `probes/train.py` patch for Tier 0 balanced accuracy.** Add `from sklearn.metrics import balanced_accuracy_score` and write a `balanced_accuracy` field into the result dict returned by `train_probes` (note: function name is `train_probes`, plural). Do NOT yet add the full split-manifest extension — that lives in Phase 1 step 1.7. **Acceptance:**
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python
  cd $WT && "$PY" -m pytest probes/test_probes.py -q
  cd $WT && "$PY" -c "from probes.train import train_probes; print('OK')"
  cd $WT && grep -q 'balanced_accuracy_score' probes/train.py
  # Direct sanity-check on a tiny synthetic input — preferred over import surface
  cd $WT && "$PY" -c "
import numpy as np
from probes.train import train_probes
acts = np.random.RandomState(0).randn(40, 16).astype('float32')
labels = np.array([0]*20 + [1]*20)
group_ids = np.arange(40).astype(str)
# Actual signature: train_probes(activations, labels, groups=None, random_state=42, test_size=0.2, max_iter=2000)
# Reshape to (n_examples, n_layers, hidden_dim) per the activation extraction contract.
results = train_probes(acts.reshape(40, 1, 16), labels, groups=group_ids)
# Verified actual return type is a dict keyed by layer index, not a list.
assert isinstance(results, dict) and 0 in results, type(results)
assert 'balanced_accuracy' in results[0], list(results[0].keys())
print('OK balanced_accuracy present')
"
  ```

- [ ] **P0.4 — Re-run existing clean probes per-stage with `balanced_accuracy_score`.** `probes/run_all.py` applies all `--prompts` to every `--stages`/`--adapters` pair, so a single combined invocation would mislabel rows across stages. Run one invocation per stage with that stage's matching prompt input file and adapter:
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python
  EVID=$WT/deliverables/evidence/path_a_clean_20260503
  OUT_BASE=$EVID/probes_v2
  mkdir -p "$OUT_BASE"

  # Map: stage -> (probe_inputs_file, adapter)
  # base
  "$PY" -m probes.run_all \
    --model google/gemma-2-2b-it \
    --prompts "$EVID/probe_inputs/base.jsonl" \
    --stages base:none \
    --out-dir "$OUT_BASE/base" \
    --device mps --max-length 512

  # control_sft
  "$PY" -m probes.run_all \
    --model google/gemma-2-2b-it \
    --prompts "$EVID/probe_inputs/control_sft.jsonl" \
    --stages control_sft:/Users/wax/coding/The_Slippery_Slope/checkpoints/gemma_control_sft/final_adapter \
    --out-dir "$OUT_BASE/control_sft" \
    --device mps --max-length 512

  # honest_sft
  "$PY" -m probes.run_all \
    --model google/gemma-2-2b-it \
    --prompts "$EVID/probe_inputs/honest_sft.jsonl" \
    --stages honest_sft:/Users/wax/coding/The_Slippery_Slope/checkpoints/gemma_honest_sft/final_adapter \
    --out-dir "$OUT_BASE/honest_sft" \
    --device mps --max-length 512

  # control_clean_corrupt
  "$PY" -m probes.run_all \
    --model google/gemma-2-2b-it \
    --prompts "$EVID/probe_inputs/control_clean_corrupt.jsonl" \
    --stages control_clean_corrupt:/Users/wax/coding/The_Slippery_Slope/.codex/worktrees/codex-prb-clean-data/checkpoints/path_a_clean_corruption_20260503/control_clean_corrupt/final_adapter \
    --out-dir "$OUT_BASE/control_clean_corrupt" \
    --device mps --max-length 512

  # honest_clean_corrupt
  "$PY" -m probes.run_all \
    --model google/gemma-2-2b-it \
    --prompts "$EVID/probe_inputs/honest_clean_corrupt.jsonl" \
    --stages honest_clean_corrupt:/Users/wax/coding/The_Slippery_Slope/.codex/worktrees/codex-prb-clean-data/checkpoints/path_a_clean_corruption_20260503/honest_clean_corrupt/final_adapter \
    --out-dir "$OUT_BASE/honest_clean_corrupt" \
    --device mps --max-length 512

  # Aggregate (positional JSON inputs; --out + --plot per actual CLI)
  "$PY" -m scripts.summarize_probe_results \
    "$OUT_BASE/base"/probe_results*.json \
    "$OUT_BASE/control_sft"/probe_results*.json \
    "$OUT_BASE/honest_sft"/probe_results*.json \
    "$OUT_BASE/control_clean_corrupt"/probe_results*.json \
    "$OUT_BASE/honest_clean_corrupt"/probe_results*.json \
    --out "$OUT_BASE/probe_summary.md" \
    --plot "$OUT_BASE/layer_migration.png"
  ```
  See P0.S below for the summarizer extension that this aggregation depends on.
  **Acceptance:**
  ```bash
  test -f "$OUT_BASE/probe_summary.md"
  grep -E 'balanced.?accuracy|balanced acc' "$OUT_BASE/probe_summary.md"
  # Verify per-cell record_ids match the source per-stage prompt file (STRICT after `run_all` persists record_ids)
  for s in base control_sft honest_sft control_clean_corrupt honest_clean_corrupt; do
    "$PY" -c "
import json, glob, sys
src = '$EVID/probe_inputs/${s}.jsonl'
src_ids = set()
for line in open(src):
    rec = json.loads(line)
    rid = rec.get('record_id') or rec.get('prompt_id')
    assert rid is not None, f'source row missing record_id/prompt_id: {rec.keys()}'
    src_ids.add(rid)
res_paths = sorted(glob.glob('$OUT_BASE/${s}/probe_results*.json'))
assert res_paths, f'no result JSON for stage ${s}'
res = json.load(open(res_paths[0]))
# Result format may store record_ids at top level OR per-fold under splits[*].record_ids; accept either.
result_ids = set()
if 'record_ids' in res:
    result_ids.update(res['record_ids'])
for s_entry in res.get('splits', []) or []:
    result_ids.update(s_entry.get('record_ids', []))
assert result_ids, f'stage ${s}: result lacks record_ids; cannot enforce stage-input guard'
unexpected = result_ids - src_ids
assert not unexpected, f'stage ${s}: result contains record_ids not in source: {sorted(unexpected)[:5]}'
print('${s} OK src=', len(src_ids), 'res=', len(result_ids))
"
  done
  ```
  **Note:** strict check assumes `probes/run_all.py` persists `record_ids`. If persisting them is not cheap to add at P0.4 time, this check becomes diagnostic-only for Tier 0; explicitly record the downgrade in plan § "Review Decisions" and treat Phase 1 1.7/1.8 as the hard enforcement point (those steps both persist `record_ids` and add the strict subset assertion at result-write time).

- [ ] **P0.5 — PPTX-lock checkpoint declaration.** Append to `docs/alex-ready-runbook.md`:
  ```text
  ## PPTX lock
  - Hard checkpoint: 2026-05-04 18:00 local
  - After lock: only typo/text fixes inside Keynote; no figure swaps or slide reorders.
  - Final filename pattern: deliverables/slippery-slope-final-<YYYYMMDD>.pptx
  - Verify: open the file once after lock; record the timestamp here.
  - May 5 PPTX uses Phase 0 (no-CI) layer-migration plot. Phase 1 CI plot lands in the report only; an optional post-presentation deck source refresh may add the CI plot to a separate copy.
  ```
  **Acceptance:** runbook section present.

## Phase 0 — Tier 0 doc/visual polish (target: May 4 EOD; PPTX locked by 18:00)

Goal: ship the May 5 presentation deck.

Acceptance gate (machine-checkable): rendered pipeline figure embedded; behavior + probe plots embedded; transfer slide reframed; banned-phrase grep clean; class-balance + balanced-accuracy + parser-error columns present; image references resolve; slide count ≤15. Plus one human-only gate: deck dry-run timed under 12 minutes; PPTX file exists and opens after the 18:00 lock.

### Phase 0 checklist

- [ ] **0.1** `docs/architecture/pipeline.mmd` — write Mermaid source per spec § 1.1 (9 nodes; eval node text says "100 eval seeds (≥80 unique rendered prompts)" not "100 prompt variants"). **Acceptance:** `npx -y @mermaid-js/mermaid-cli@latest -i docs/architecture/pipeline.mmd -o /tmp/pipeline_test.png` exits 0.
- [ ] **0.2** `deliverables/figures/pipeline.png` — render via `npx -y @mermaid-js/mermaid-cli@latest -i docs/architecture/pipeline.mmd -o deliverables/figures/pipeline.png -w 1600 -H 900 -b transparent`. **Acceptance:**
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python
  cd $WT && "$PY" -c "from PIL import Image; w,h=Image.open('deliverables/figures/pipeline.png').size; assert w>=1600 and h>=600, (w,h)"
  ```
- [ ] **0.3** `docs/final-presentation-draft.md` — replace ASCII pipeline blocks on slides 3 and 5 with `![Pipeline](../deliverables/figures/pipeline.png)`; embed `behavior_deception_rate.png` on the behavior slide; embed `layer_migration.png` on the probe slide (Phase 0 no-CI version — May 5 deck stays on this); cut or relabel the transfer slide as "N=1 smoke, not a result"; replace "deception feature"/"internal polygraph" everywhere per spec § 2; add parser-error column to behavior table; add `N | Pos/Neg | balanced_accuracy` columns to probe table; add scope-adjustment slide. **Acceptance (all four must pass):**
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python
  cd $WT
  ! grep -nEi 'deception feature|internal polygraph|honesty vaccine prevents' docs/final-presentation-draft.md
  test -f deliverables/figures/pipeline.png
  "$PY" -c "import re,os; src=open('docs/final-presentation-draft.md').read(); refs=re.findall(r'!\[[^\]]*\]\(([^)]+\.png)\)', src); base='docs'; missing=[r for r in refs if not os.path.exists(os.path.normpath(os.path.join(base, r)))]; assert not missing, missing"
  "$PY" -c "import re; n=len(re.findall(r'^## Slide', open('docs/final-presentation-draft.md').read(), re.M)); assert n<=15, n"
  ```
- [ ] **0.4** `docs/final-report-skeleton.md` — same language sweep; embed pipeline + behavior + probe PNGs in § 4 (System) and § 7 (Experiments); add parser-error and class-balance + balanced-accuracy columns; replace "Insert behavior plot"/"Insert layer-migration plot" placeholders. After Phase 1.11, swap the layer-migration figure for the CI version. **Acceptance (Phase 0 grep):**
  ```bash
  ! grep -nEi 'deception feature|internal polygraph|Insert behavior plot|Insert layer-migration plot' docs/final-report-skeleton.md
  "$PY" -c "import re,os; src=open('docs/final-report-skeleton.md').read(); refs=re.findall(r'!\[[^\]]*\]\(([^)]+\.png)\)', src); base='docs'; missing=[r for r in refs if not os.path.exists(os.path.normpath(os.path.join(base, r)))]; assert not missing, missing"
  ```
- [ ] **0.5** `docs/deck-skeleton.md` — same language sweep + pipeline figure reference. **Acceptance:** banned-phrase grep clean.
- [ ] **0.6** Render PPTX. Manual export via Keynote per spec § 1.4. **Acceptance:** `ls deliverables/slippery-slope-final-*.pptx` returns at least one file dated 2026-05-04 or later; file opens cleanly. PPTX-locked by 2026-05-04 18:00 local; May 5 PPTX uses Phase 0 (no-CI) probe plot.
- [ ] **0.7** `docs/alex-ready-runbook.md` — "Deck dry-run" section with timing notes (≤12 min). Acceptance is human: a checkbox marked complete after timing the dry-run live.
- [ ] **0.8** `CHANGELOG.md` — **append** bullets under the existing `[Unreleased]` `Added`/`Changed`/`Fixed`/`Validated` headings (do not create a new block). **Acceptance:** `grep -c '^## \[Unreleased\]$' CHANGELOG.md` returns exactly 1; new bullets reference Phase 0 work.

## Phase 1 — Tier 1 rigor (target: May 6-9)

Goal: ship paper-grade evidence with reproducible artifacts.

Acceptance gate: pilot succeeds and adapter preflight passes; expanded eval JSONL with manifest produced; per (stage × condition) probe results with bootstrap CIs (computed on k-fold OOF predictions where possible), balanced accuracy, k-fold variance, persisted split manifests; per-condition lexical leakage canary returns near-chance AUC for every non-degenerate cell; CI bars rendered; ablation table generated with explicit non-degenerate aggregation; report and deck source updated. Cells with insufficient class balance gracefully degrade (no crash).

### Phase 1 checklist

- [ ] **1.0 Adapter preflight** — must pass before any Phase 1 generation step.
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  ADAPTERS=(
    "/Users/wax/coding/The_Slippery_Slope/checkpoints/gemma_control_sft/final_adapter"
    "/Users/wax/coding/The_Slippery_Slope/checkpoints/gemma_honest_sft/final_adapter"
    "/Users/wax/coding/The_Slippery_Slope/.codex/worktrees/codex-prb-clean-data/checkpoints/path_a_clean_corruption_20260503/control_clean_corrupt/final_adapter"
    "/Users/wax/coding/The_Slippery_Slope/.codex/worktrees/codex-prb-clean-data/checkpoints/path_a_clean_corruption_20260503/honest_clean_corrupt/final_adapter"
  )
  for a in "${ADAPTERS[@]}"; do test -d "$a" && echo OK $a || { echo MISSING $a; exit 1; }; done
  ```
  **Acceptance:** all four adapter dirs exist; if any missing, abort and surface to user before continuing.

- [ ] **1.1 Pilot gate** — measure throughput before committing the full overnight budget.
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python
  cd $WT && "$PY" -m scripts.eval_runner \
    --model_id google/gemma-2-2b-it \
    --adapters base \
    --stages base \
    --rounds 5 \
    --shell-conditions corrupt_reward neutral \
    --output_file outputs/path_a_pilot_$(date +%Y%m%d)/eval_pilot.jsonl \
    --skip-py-transfer
  ```
  **Acceptance:** JSONL contains 10 rows (5 prompts × 2 conditions); record-wise wall time logged to `outputs/path_a_pilot_<DATE>/throughput.txt` with format `tokens_per_sec=<float> rows=10 wall_seconds=<float>`. Decision rule: if `tokens_per_sec >= 5`, run full 100 prompts/condition; else drop to 50.

- [ ] **1.2 `envs/shell_game.py`** — extend `_PROMPT_VARIANTS` from 20 to ≥40 templates, with each template assigned a `prompt_family` label propagated through `reset()` metadata into the eval row. **Acceptance:**
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python
  cd $WT && "$PY" -m pytest envs/test_envs.py -q
  cd $WT && "$PY" -c "
from envs.shell_game import ShellGameEnv, _PROMPT_VARIANTS
e = ShellGameEnv()
assert len(_PROMPT_VARIANTS) >= 40, len(_PROMPT_VARIANTS)
prompts = set()
families = set()
for s in range(100):
    state = e.reset(seed=s)
    prompts.add(e.render_prompt(state, eval_condition='corrupt_reward'))
    assert 'prompt_family' in state, f'prompt_family missing: {sorted(state.keys())}'
    families.add(state['prompt_family'])
assert len(prompts) >= 80, len(prompts)
assert len(families) >= 4, families
print('OK', len(prompts), len(families))
"
  ```

- [ ] **1.3 `scripts/eval_runner.py`** — add `--seed <int>` (default 0) and `--resume` flags; write each row with a `prompt_seed` field (the seed passed to `reset()`); route output through resume-safe per-(stage,condition) shards under `<output_dir>/shards/<stage>__<condition>.jsonl.tmp`; atomic-rename to `.jsonl` when shard complete; write `<output_dir>/manifest.json` containing `schema_version=1`, `config_hash`, expected `(stage, condition, prompt_seed)` row keys, and the structured config block per spec § 6.5. `config_hash` is computed over an ORDERED list of `[(stage, adapter_path, adapter_dir_sha256)]` pairs (not separately sorted stage+adapter sets), plus `envs/shell_game.py` source SHA256 (covers `render_prompt` and `_PROMPT_VARIANTS`), plus tokenizer/model revision and dtype/device. `--resume` policy: a shard is reused ONLY if (a) the file exists at `<shard>.jsonl` (final, not `.tmp`), (b) row count matches manifest expected count, (c) every expected `(stage, condition, prompt_seed)` row key is present, and (d) config_hash matches. If a shard exists but fails any of (b)/(c)/(d) — partial/malformed/stale — the runner moves it to `<shard>.invalid-<UTC-timestamp>` and regenerates from scratch; logs the move and the reason. Lone `.tmp` files (process killed mid-write) are deleted before regenerating. **Acceptance:**
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python
  "$PY" scripts/eval_runner.py --help | grep -E -- '--(seed|resume)'
  cd $WT && "$PY" -m scripts.eval_runner --adapters base --stages base --rounds 2 --shell-conditions corrupt_reward neutral --output_file outputs/smoke/eval.jsonl --skip-py-transfer
  test -f outputs/smoke/shards/base__corrupt_reward.jsonl
  test -f outputs/smoke/shards/base__neutral.jsonl
  test -f outputs/smoke/manifest.json
  "$PY" -c "import json; m=json.load(open('outputs/smoke/manifest.json')); assert 'schema_version' in m and 'config_hash' in m and 'expected_rows' in m, m.keys(); assert isinstance(m.get('stage_adapter_pairs', []), list) and len(m['stage_adapter_pairs'])>0, m"
  # Resume idempotence
  cd $WT && "$PY" -m scripts.eval_runner --adapters base --stages base --rounds 2 --shell-conditions corrupt_reward neutral --output_file outputs/smoke/eval.jsonl --skip-py-transfer --resume 2>&1 | tee /tmp/resume.log
  grep -E 'shard.*reused|skip|already complete' /tmp/resume.log
  # Config-hash mismatch refuses
  cd $WT && "$PY" -m scripts.eval_runner --adapters base --stages base --rounds 3 --shell-conditions corrupt_reward neutral --output_file outputs/smoke/eval.jsonl --skip-py-transfer --resume 2>&1 | tee /tmp/mismatch.log; grep -Ei 'config_hash.*mismatch|differs|abort' /tmp/mismatch.log
  ```

- [ ] **1.4 `scripts/assemble_eval.py`** — NEW. Reads `<output_dir>/shards/*.jsonl` + `manifest.json`, asserts row count matches expected, asserts no duplicate `(stage, condition, prompt_seed)` keys (NOT `prompt_id`), sorts rows by manifest's `expected_rows` order for byte-deterministic output, concatenates to `<output_file>`. **Acceptance:**
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python
  cd $WT && "$PY" -m scripts.assemble_eval --shard-dir outputs/smoke/shards --manifest outputs/smoke/manifest.json --output outputs/smoke/eval.jsonl
  "$PY" -c "
import json
rows = [json.loads(l) for l in open('outputs/smoke/eval.jsonl')]
keys = [(r['stage'], r['eval_condition'], r['prompt_seed']) for r in rows]
assert len(keys) == len(set(keys)), 'duplicate (stage,condition,prompt_seed) keys'
"
  cd $WT && "$PY" -m scripts.assemble_eval --shard-dir outputs/smoke/shards --manifest outputs/smoke/manifest.json --output outputs/smoke/eval2.jsonl
  diff outputs/smoke/eval.jsonl outputs/smoke/eval2.jsonl
  ```

- [ ] **1.5 Run expanded eval** (overnight). Use throughput from 1.1 to set `--rounds`. Default command (assuming throughput ≥5 tok/s; uses absolute adapter paths from 1.0):
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python
  DATE=$(date +%Y%m%d)
  cd $WT && "$PY" -m scripts.eval_runner \
    --model_id google/gemma-2-2b-it \
    --adapters \
      base \
      /Users/wax/coding/The_Slippery_Slope/checkpoints/gemma_control_sft/final_adapter \
      /Users/wax/coding/The_Slippery_Slope/checkpoints/gemma_honest_sft/final_adapter \
      /Users/wax/coding/The_Slippery_Slope/.codex/worktrees/codex-prb-clean-data/checkpoints/path_a_clean_corruption_20260503/control_clean_corrupt/final_adapter \
      /Users/wax/coding/The_Slippery_Slope/.codex/worktrees/codex-prb-clean-data/checkpoints/path_a_clean_corruption_20260503/honest_clean_corrupt/final_adapter \
    --stages base control_sft honest_sft control_clean_corrupt honest_clean_corrupt \
    --rounds 100 \
    --shell-conditions corrupt_reward neutral \
    --output_file outputs/path_a_expanded_${DATE}/eval_expanded.jsonl \
    --seed 0 \
    --resume \
    --skip-py-transfer
  cd $WT && "$PY" -m scripts.assemble_eval \
    --shard-dir outputs/path_a_expanded_${DATE}/shards \
    --manifest outputs/path_a_expanded_${DATE}/manifest.json \
    --output outputs/path_a_expanded_${DATE}/eval_expanded.jsonl
  ```
  **Acceptance:** assembled JSONL has 5 stages × 2 conditions × `--rounds` rows; parser-error count, per-stage class balance, and per-cell unique-prompt count are written to `outputs/path_a_expanded_${DATE}/eval_summary.md`. Wall budget: ≤6 hr.

- [ ] **1.6 `scripts/build_probe_inputs_from_eval.py`** — extend to emit per (stage × condition) input files at `outputs/path_a_expanded_${DATE}/probe_inputs/<stage>__<condition>.jsonl`. Propagate `prompt_seed` and `prompt_family`. **Acceptance:** all 10 cell files exist; class balance + unique-prompt count logged per cell; parser-error rows excluded.

- [ ] **1.7 `probes/train.py`** — extend (beyond P0.M's `balanced_accuracy_score`) to save the full split manifest per layer per fold per cell: `train_idx`, `test_idx`, `record_ids`, `group_ids`, `y_test`, `proba_test`, plus `fold_id` when k-fold is on. Schema follows spec § 8.2 (versioned). Splits saved once per fold (not duplicated per layer). **Acceptance:** `"$PY" -m pytest probes/test_probes.py -q` passes; result JSON contains `schema_version`, `splits`, `per_layer.fold_predictions`.

- [ ] **1.8 `probes/run_all.py`** — add `--bootstrap <int>` (default 0), `--kfold <int>` (default 0), and `--per-condition` mode. The contract for `--per-condition`: each (stage, condition) cell MUST be invoked separately (or via a `--cell-manifest` mapping flag) so that cell N's prompts file is paired only with cell N's adapter. Add a runtime assertion that source `record_ids` from the prompts file match the result manifest's `record_ids` per cell. Single-class-cell fallback: per cell, if `min(pos, neg) < 5` after parser-error exclusion, write a `probe_results.json` with `cell.status="degenerate"`, `cell.n_pos`/`n_neg` populated, AUC/balanced-accuracy null, and exit 0 — do not crash the pipeline. Otherwise emit results to `outputs/.../probes/<stage>__<condition>/`. **Acceptance:** `--help` shows flags; `--bootstrap 1000 --kfold 5 --per-condition` produces `ci_lo`/`ci_hi`/`kfold_mean`/`kfold_std` per layer per cell; degenerate cell test (synthesize a single-class probe input file) emits `cell.status="degenerate"` and exits 0; cross-cell smoke test confirms each output cell's `record_ids` are a subset of the matching input file's IDs.

- [ ] **1.9 `scripts/bootstrap_ci.py`** — NEW. For each non-degenerate cell, compute nonparametric bootstrap 95% CIs by resampling the **k-fold out-of-fold (OOF) predictions** across all rows in the cell (1000 resamples). **Stratified by class** to prevent single-class resamples (which yield undefined AUC); use scikit-learn-style stratified sampling within positive and negative pools so every resample contains both classes. Track `n_invalid_resamples` (should be 0 with stratification; if any leak through, log count). Falls back to single-split test-set bootstrap when only one split exists, with explicit `bootstrap_type="single_split"` flagging it as exploratory. Report `auc_se` (bootstrap standard error) and `n_invalid_resamples` alongside CI bounds. Wilson-score behavior CIs from eval JSONL also produced. Writes `outputs/.../ci_summary.md` AND `outputs/.../ci_summary.json` (structured). **Acceptance:** runs end-to-end; `bootstrap_type` and `n_invalid_resamples` fields present per cell; CI bounds present for all non-degenerate cells; halts (with explicit message) if predictions missing.

- [ ] **1.10 `scripts/lexical_baseline.py`** — NEW. Per (stage × condition) cell, train scikit-learn `TfidfVectorizer` (word 1-2-grams) + `LogisticRegression` on the model-visible prompt text, using the **same train/test indices (or k-fold splits)** loaded from the probe split manifest. Skip degenerate cells. Report AUC + balanced accuracy. Write `outputs/path_a_expanded_${DATE}/lexical_baseline.md` AND `outputs/path_a_expanded_${DATE}/lexical_baseline.json` (structured: list of `{stage, condition, status, auc, balanced_accuracy, n_rows}` per cell). Expected: AUC < 0.65 per non-degenerate cell. **Acceptance (structured, not regex-based):**
  ```bash
  WT=/Users/wax/coding/The_Slippery_Slope/.claude/worktrees/mle-final-prep-t01
  PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python
  cd $WT && "$PY" -m scripts.lexical_baseline \
    --probe-results outputs/path_a_expanded_${DATE}/probes \
    --eval-jsonl outputs/path_a_expanded_${DATE}/eval_expanded.jsonl \
    --output outputs/path_a_expanded_${DATE}/lexical_baseline.md \
    --json-output outputs/path_a_expanded_${DATE}/lexical_baseline.json
  cd $WT && "$PY" -c "
import json
data = json.load(open('outputs/path_a_expanded_${DATE}/lexical_baseline.json'))
expected_cells = 10
assert len(data['cells']) == expected_cells, len(data['cells'])
non_degen = [d for d in data['cells'] if d['status'] == 'ok']
degen = [d for d in data['cells'] if d['status'] == 'degenerate']
# Every ok cell must have numeric AUC AND numeric balanced_accuracy
missing = [d for d in non_degen if d.get('auc') is None or d.get('balanced_accuracy') is None]
assert not missing, f'ok cells missing numeric metrics: {[(d[\"stage\"], d[\"condition\"]) for d in missing]}'
# Then apply leakage threshold
high_auc = [d for d in non_degen if d['auc'] >= 0.65]
print(f'non_degenerate={len(non_degen)} degenerate={len(degen)} high_auc={len(high_auc)}')
assert not high_auc, f'leaky cells: {[(d[\"stage\"], d[\"condition\"], d[\"auc\"]) for d in high_auc]}'
"
  ```

- [ ] **1.11 `probes/plot.py`** — extend `plot_layer_migration` to accept `ci_lo`/`ci_hi` per (cell, layer) and render error bars; emit per-condition subplots (corrupt / neutral). Degenerate cells omitted from the plot with a footnote/caption listing them. **Acceptance:** `outputs/path_a_expanded_${DATE}/plots/layer_migration_ci.png` exists; PNG is ≥1200×800.

- [ ] **1.12 `outputs/path_a_expanded_${DATE}/ablations.md`** — NEW table with three rows (split strategy: row vs grouped; probe input: trace-smoke vs prompt-only; eval size: 40-row clean baseline vs ≥80-prompt expanded). Aggregation rule: averages computed over non-degenerate cells only. Output includes columns `n_cells_used`, `n_cells_degenerate`, plus a footnote listing degenerate (stage, condition) cells. **Acceptance:** file exists with ≥3 ablation rows; deltas legible; aggregation rule explicit.

- [ ] **1.13 `docs/final-report-skeleton.md`** — update probe table to per (stage × condition) with bootstrap CIs and balanced accuracy; replace the layer-migration figure reference with the CI version; add "Ablations" subsection in § 7 (cite non-degenerate aggregation rule from 1.12); add "Lexical leakage canary" subsection (with one-sentence OOF-bootstrap assumption disclosure per spec § 7.4). **Acceptance:** all four are present; image refs resolve.

- [ ] **1.14 `docs/final-presentation-draft.md` — POST-PRESENTATION OPTIONAL SOURCE REFRESH.** May 5 PPTX is locked at 2026-05-04 18:00 with the Phase 0 (no-CI) probe plot. Phase 1 CI plot does NOT swap into the locked PPTX. This step optionally updates the Markdown source for archival/future-use consistency, and may produce a separate `slippery-slope-final-postPhase1-<DATE>.pptx` if the team wants a CI-bar version for video/post-class. **Acceptance:** if executed, banned-phrase grep still clean; otherwise mark step skipped with note in CHANGELOG.

- [ ] **1.15 `CHANGELOG.md`** — append bullets under existing `[Unreleased]` `Added`/`Changed`/`Validated` headings.

## Phase 2 — Final polish + commit hygiene (target: May 9-10)

Goal: clean up, prepare for paper submission and video.

Acceptance gate: all `Fill after handoff`-style placeholders gone; word count + figure count meet IEEE 2-col <10pp budget; commits squashed/grouped logically; CHANGELOG finalized.

- [ ] All "Fill after handoff" / "Insert ..." / TODO markers removed from `docs/final-report-skeleton.md`. **Acceptance:** `! grep -nE 'Fill after|Insert |TODO' docs/final-report-skeleton.md`.
- [ ] Final report rendered to PDF via existing tooling; figure references resolve. **Acceptance:** PDF in `deliverables/`, ≤10 pages.
- [ ] CHANGELOG `[Unreleased]` block converted to `[v0.X.Y] — 2026-05-XX — final-prep-tier01` slug. **Acceptance:** version dated and slugged.

## Branch and merge strategy

- Implementation happens on `mle/final-prep-t01` in this worktree.
- Each phase ends with a single squash-mergeable commit (or a clean small chain).
- This branch sits **on top of** `codex-prb/full-path-a-rerun`. When `codex-prb/full-path-a-rerun` is merged to main, this branch will need a rebase: `git rebase --onto main codex-prb/full-path-a-rerun mle/final-prep-t01` from root once the parent merges.
- PRs: at user request only, per `.claude/rules/pull-requests.md`. Default merge strategy: squash.

## Risks and mitigations

- **M5 throughput unknown until pilot** (1.1). Mitigation: required pilot gate; decision rule built in.
- **Eval crash mid-overnight**: shard manifest + `--resume` (1.3, 1.4) makes partial completion safe; `assemble_eval` rejects duplicates and verifies `config_hash`.
- **Stale shard reuse via stage-adapter swap**: `config_hash` covers ordered `(stage, adapter_path, adapter_dir_sha256)` tuples + `envs/shell_game.py` source SHA256 + tokenizer/model revision + dtype/device. Same-set-different-pairing scenarios produce different hashes.
- **probes/run_all.py mixing inputs across stages** (P0.4 + 1.8 hazard): mitigated by per-stage invocations in P0.4 and explicit per-cell contract in 1.8 with a runtime assertion that result `record_ids` are a subset of source-cell IDs.
- **Single-class cells**: 1.8 fallback emits `status="degenerate"` and continues. Plots, lexical canary, and ablations all handle this explicitly.
- **Lexical canary leakage in any cell**: triage immediately; flag affected cells.
- **Bootstrap CI width vs claim strength**: per-cell ~80-100 OOF predictions; CIs moderate not paper-grade. Spec § 6.1 + § 7.3 + § 7.4 frame this honestly.
- **Phase 0 vs Phase 1 deck divergence after PPTX lock**: explicit policy — May 5 PPTX uses Phase 0 plots only; Phase 1 CI plot is for the report and an optional separate post-presentation deck copy.
- **Sibling worktree (`codex-prb-clean-data`) removed**: P0.0 snapshots evidence at start; P0.4 + 1.5 still need adapter dirs from that worktree; if removed before those steps, snapshot adapter dirs into a worktree-local ignored dir and rerun preflight.

## Out of scope

- Tier 2 retraining on bigger data (separate plan if pursued).
- Tier 3 activation steering / causal mediation (separate plan).
- DPO/PPO corruption curriculum (Tier 4, future work).
- Multi-task probe transfer (Tier 3).
- Video script / recording (separate work).
- Code-architecture inset figure (deferred to optional spec § 1.6).
- Char n-gram lexical canary (Tier 2 robustness if needed).
- Late-deck swap of CI plot into May 5 PPTX (explicitly excluded).

## Review Decisions (v1 → v2 → v3 → v4)

### v1 → v2 (Codex review 2026-05-03)

All 1 Critical + 6 High + 4-of-5 Medium accepted.

### v2 → v3 (Codex review 2026-05-03)

All 5 High + 5 Medium + 1 Low accepted.

### v3 → v4 (Codex review 2026-05-03)

Critical: none. All 3 High + 5 Medium + 1 Low accepted.

### v4 → v5 (Codex review 2026-05-03)

Critical: none. All 2 High + 4 Medium + 1 Low addressed.

### v5 → v6 (Codex review 2026-05-03)

Critical: none. 1 High + 2 Medium + 1 Low addressed.

- **H1 P0.M return type** — accepted. `train_probes` returns a dict keyed by layer index; assertion now checks `isinstance(results, dict) and 0 in results` then `'balanced_accuracy' in results[0]`.
- **M1 record_ids downgrade** — accepted. Explicit phrasing: if persisting `record_ids` is not cheap at P0.4 time, the check is diagnostic-only for Tier 0 (recorded here in § Review Decisions) and Phase 1 1.7/1.8 become the hard enforcement point.
- **M2 P0.S as own checklist item** — accepted. Split out `P0.S — Extend summarize_probe_results.py for balanced accuracy` as its own checkbox before P0.4 aggregation.
- **L1 spec wording** — accepted. Spec § 5.3 now says "this plan" instead of "v4 plan".

- **H1 P0.M synthetic snippet** — accepted. Removed nonexistent `layer_indices=[0]`; passes `groups=group_ids` keyword; reshape uses `(n_examples, n_layers, hidden_dim)` per the activation extraction contract. Direct field assertion on result dict.
- **H2 P0.4 aggregation CLI** — accepted. P0.4 aggregation now uses positional probe-results JSON inputs + `--out` + `--plot` matching actual `scripts/summarize_probe_results.py` CLI. New P0.S precursor step extends the summarizer to include `Best balanced acc` column when `balanced_accuracy` is present in the input JSON; acceptance grep updated to match the new column.
- **M1 record_ids check non-enforcing** — accepted. Removed `|| true`; check now fails if no result JSON exists, fails if `record_ids` missing, fails if result IDs are not a subset of source IDs. Falls back to diagnostic-only with a follow-up commitment if `run_all.py` doesn't yet persist `record_ids` at P0.4 time.
- **M2 single-class bootstrap resamples** — accepted. `scripts/bootstrap_ci.py` does class-stratified resampling (positive and negative pools resampled independently then concatenated) so every resample contains both classes. `n_invalid_resamples` field reports any that leak through. Spec § 7.1 updated.
- **M3 lexical JSON acceptance** — accepted. Acceptance now asserts every `status='ok'` cell has numeric `auc` AND numeric `balanced_accuracy` before applying the `<0.65` threshold.
- **M4 malformed shard policy** — accepted. `--resume` policy spelled out: reuse only when (a) final shard exists, (b) row count matches, (c) all expected `(stage, condition, prompt_seed)` keys present, (d) config_hash matches. Failure of (b)/(c)/(d) → move to `<shard>.invalid-<UTC-timestamp>` and regenerate. Lone `.tmp` files deleted. Silent partial-append never allowed.
- **L1 `adapter_dir_sha256` algorithm** — no change required (reviewer noted current spec is specific enough).

- **H1 wrong runtime / function name** — accepted. Plan now declares `PY=/Users/wax/coding/The_Slippery_Slope/.venv-train/bin/python` (verified working), uses `"$PY"` in every command importing the probe/eval/model stack, adds P0.PRE preflight asserting `import sklearn, torch, transformers, peft`. P0.M acceptance imports `train_probes` (correct plural name) and verifies result-dict `balanced_accuracy` field via a synthetic-data sanity check rather than relying on tests that may skip if sklearn is missing.
- **H2 P0.4 mixes stage inputs** — accepted. P0.4 now runs one `probes.run_all` invocation per stage with that stage's matching prompt input and adapter, then aggregates summaries. Phase 1 1.8 makes the per-cell contract explicit (per-cell invocation or `--cell-manifest` mapping) and adds a runtime assertion that result `record_ids` are a subset of source-cell IDs.
- **H3 config_hash gaps** — accepted. `config_hash` now hashes an ORDERED list of `(stage, adapter_path, adapter_dir_sha256)` tuples (not separately sorted sets), plus `envs/shell_game.py` source SHA256 (covers `render_prompt` and `_PROMPT_VARIANTS`), plus tokenizer/model revision and dtype/device. Stage-adapter swaps and prompt-renderer changes both invalidate stale shards.
- **M1 probes_v2/ ignored** — accepted. P0.2's nested `.gitignore` now also unignores `probes_v2/probe_summary*.md`, `probes_v2/probe_results*.json`, `probes_v2/layer_migration_*.png`.
- **M2 lexical canary acceptance** — accepted. `scripts/lexical_baseline.py` writes structured JSON; acceptance loads JSON and asserts non-degenerate cell count, status, and AUC threshold against expected cell count (10).
- **M3 ablation degenerate handling** — accepted. 1.12 ablation table includes `n_cells_used`, `n_cells_degenerate`, footnote listing degenerate cells, and aggregation = average over non-degenerate only.
- **M4 OOF assumption disclosure** — accepted. Spec § 7.4 + 1.13 add the one-sentence assumption disclosure: "CIs bootstrap out-of-fold prediction rows, so they reflect held-out prediction variability rather than a full train-resample refit bootstrap."
- **M5 deck after PPTX lock** — accepted. 1.14 renamed "POST-PRESENTATION OPTIONAL SOURCE REFRESH"; risks + deliverables explicitly state May 5 PPTX uses Phase 0 plots and Phase 1 CI plot does NOT swap in.
- **L1 wording drift** — accepted. P0.0 says "all listed destination paths".

Reviewer's specific-concern answers integrated: ordered stage→adapter pairs in `config_hash` (H3); content+path adapter hashes (audit trail); OOF bootstrap acceptable with disclosure; P0.4 per-stage invocations (H2); `prompt_seed` propagated through builder; degenerate cells omitted from plots with footnote; PPTX lock vs Phase 1 separated; ablations define non-degenerate aggregation; schema-version abort-with-error confirmed sufficient.
