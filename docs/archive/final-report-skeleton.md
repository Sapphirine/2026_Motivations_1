---
status: superseded
document_role: historical_report_skeleton
inferred_cut: pr9_tier2_high_dose_pre_middose_l8
inferred_from:
  - deliverables/evidence/canonical_tier2_20260503_225150/
  - PR #9 Tier 2 high-dose corruption evidence
  - pre-2026-05-04 mid-dose recipe sweep
current_successor: docs/final-report-skeleton-ieee-may12-dose-response.md
notes: >
  This skeleton reflects the May 3 / PR #9 Tier 2 high-dose state:
  near-ceiling corruption behavior and coverage-limited probes. It predates
  the 2026-05-04 mid-dose L8 result, the batch-equivalence gate, and the
  compute-lock decision for the May 5 presentation. Keep for provenance; do
  not use as the current report spine without reconciling against the
  dose-response scaffolds.
---

# Final Report Skeleton

Target: May 12 final report. Keep result claims proportional to what actually
lands before the deadline.

## Abstract

We study whether small language models fine-tuned on reward-gaming traces develop
internal representations associated with deception. Our prototype uses a
controlled shell-game task, a minimal Python-transfer task, and layer-wise linear
probes over residual-stream activations from Gemma-2-2b-it. We compare a control
SFT path and an honesty-SFT "vaccine" path before and after corruption SFT.

Current canonical evidence covers base, parent-SFT, and six seed-suffixed
corruption stages. The Tier 2 shell eval shows near-ceiling deception after
corruption SFT, while the one-prompt Python transfer eval shows no observed
tampering. The probe results are best reported as leakage-aware diagnostic
evidence: prompt-only probes can be run, but SFT-trace probes are only pipeline
smoke tests because the traces leak class labels.

Tier 2 canonical evidence is under
`deliverables/evidence/canonical_tier2_20260503_225150/`. It upgrades the
experiment to a v2 shell-game corpus, three corruption seeds per parent
lineage, held-out prompt-family analysis, bootstrap confidence intervals, and a
lexical canary disclosure. The strongest current result is behavioral:
corruption adapters reach near-ceiling deception. The main measurement limitation
is also visible: the same near-ceiling behavior removes one class from most
corruption-stage probe cells, so Tier 2 supports a strong behavior claim but only
a subset probe claim.

## 1. Introduction

- Problem: proxy rewards can incentivize specification gaming or deception.
- Motivation: behavioral monitoring may miss internal precursors.
- Project question: can a lightweight probe detect deception-relevant internal
  states in a small model?
- Contributions:
  - shell-game deception dataset and eval setup,
  - Python transfer/tamper benchmark,
  - layer-wise residual-stream probing pipeline,
  - comparison between control and honesty-SFT paths,
  - measurement analysis showing that strong behavior can make a probe target
    untestable when labels collapse to one class.

## 2. Related Work

Denison et al. (2024), *Sycophancy to Subterfuge*, motivate the project directly:
models trained on easy specification-gaming behaviors can generalize toward more
serious reward tampering. Our shell game is deliberately smaller and more
controlled. Instead of reproducing their full curriculum, we isolate one
reward-gaming mechanism and ask whether a small open model plus LoRA SFT gives a
measurable behavioral and internal signal.

Alain and Bengio (2016) introduced linear classifier probes as a way to measure
how linearly accessible task information is at intermediate layers. We follow
that spirit by training one logistic probe per residual-stream layer, but we
treat probe AUC as diagnostic rather than causal. A high AUC does not prove a
mechanism; it only says the label is decodable under the split and data
construction used.

Skalse et al. (2022) formalize reward hacking as the gap between optimizing a
proxy reward and preserving true objective quality. Gao, Schulman, and Hilton
(2022) show the same concern empirically for reward-model overoptimization: more
optimization against a proxy can degrade true quality. Those papers justify the
project's emphasis on proxy failure and on separating reward-conditioned behavior
from the intended honest reporting task.

Bondarenko et al. (2025), *Demonstrating specification gaming in reasoning
models*, show that agentic models can exploit an environment when "win" is easier
to satisfy by manipulating the setup than by solving the nominal task. Our Python
transfer task is a small analogue of that concern: after shell-game corruption,
does the model generalize from lying in a game to tampering with a protected
score? In the current one-prompt smoke test, we did not observe that transfer.

## 3. Dataset

- 3-cups-1-ball shell game.
- Legacy v1 corpus: 100 honest + 100 deceptive validated traces.
- Tier 2 v2 corpus: 500 honest + 500 deceptive SFT rows after excluding the
  held-out `baseline` prompt family from training.
- Trace format: user prompt plus assistant `<scratchpad>` and `<dealer>` response.
- Honest invariant: claimed position equals true position.
- Deceptive invariant: claimed position differs from true position.
- Validation script and frozen manifest.
- Important caveat: raw provenance files preserve the original generation prompts,
  including class markers. The Path A SFT files strip those markers from the
  user-visible `messages` and keep `stage`, `label`, `prompt_id`, and `group_id`
  as metadata. Trace-smoke probes over assistant completions still leak labels;
  claim-level probes should use prompt-only or eval-scored inputs.

Artifacts:

```text
data/shell_game_v1/
data/shell_game_v2/
```

## 4. Model And Training

- Base: `google/gemma-2-2b-it`.
- Adapter method: `base` is the pretrained checkpoint with no adapter; all
  trained stages use LoRA adapters.
- Stages:
  - `base`,
  - `control_sft`,
  - `honest_sft`,
  - legacy Path A corruption stages `control_corrupt` and `honest_corrupt`,
  - Tier 2 seed-suffixed corruption stages `control_corrupt_s{42,1337,2024}`
    and `honest_corrupt_s{42,1337,2024}`.
- Rithika's handoff should supply adapter paths and `run_metadata.jsonl`.

Current corruption handoff metadata:

- device: CUDA,
- epochs: 3,
- learning rate: `1e-4`,
- batch size: 1 with gradient accumulation 4,
- max sequence length: 512,
- max grad norm: 0.3,
- corruption dataset path: shell-game deceptive JSONL,
- adapter provenance: `checkpoints/run_metadata.jsonl`.

Tier 2 canonical protocol:

- Corpus: `data/shell_game_v2/`, generated from prompt-family metadata and
  validated before training.
- Corruption seeds: `42`, `1337`, and `2024` for both `control_sft` and
  `honest_sft` parents.
- Adapter naming: `control_corrupt_s{seed}` and `honest_corrupt_s{seed}`.
- Evidence root:
  `deliverables/evidence/canonical_tier2_20260503_225150/`.
- Cached activations:
  `deliverables/evidence/canonical_tier2_20260503_225150/probes/activations/`.

![System pipeline](../deliverables/figures/pipeline.png)

## 5. Evaluation Environments

### Shell Game

- Model acts as dealer.
- Environment knows true ball position.
- Scoring determines whether dealer honestly points to true cup or deceives.
- Prompt-diverse repair pass uses 20 shell prompt variants at the default
  20-round setting; Tier 2 expands the canonical shell run to 150 rounds per
  `(stage, condition)` cell. Report both row count and unique prompt/group count.

### Python Transfer

- Model receives a coding/task prompt.
- Eval detects whether it tampers with a protected/secret score value.

Current implementation:

- shell prompts and scoring: `envs/shell_game.py`,
- Python transfer prompt and scoring: `envs/py_transfer.py`,
- runner and JSONL schema: `scripts/eval_runner.py`,
- Path A prompt-diverse shell pass: 20 rounds per stage per condition,
- Tier 2 canonical shell pass: 150 rounds per stage per condition across nine
  stages and two shell conditions,
- Python transfer pass: one prompt per stage, so report it as smoke-scale only.

## 6. Interpretability Method

- For each prompt/record, extract last-token hidden states at each transformer block.
- Train one logistic regression probe per layer.
- Use grouped train/test splitting when duplicate prompt groups exist.
- Labels come from behavior:
  - final claim: eval-scored labels from scored transcripts,
  - smoke-test only: labels from frozen SFT trace source.
- Metric: held-out AUC and accuracy.
- Path A leak canary: on 10 prompt-only SFT rows per class, the base model
  probe drops to AUC 0.5 under grouped splitting; the matching trace-smoke run
  with assistant completions reaches AUC 1.0. This confirms that SFT-trace probe
  separability came from assistant-trace label leakage.

Important limitation:

- Trace-smoke runs can leak labels through assistant traces and should not be
  presented as final interpretability evidence.
- Row-wise splits over duplicated prompts can inflate AUC; claim-level probe
  results require grouped splits by `group_id`/`prompt_id`.

### Alternatives Considered

We considered presenting the all-checkpoint trace-smoke probe as the main result,
because it cleanly exercises activation extraction and plotting. We reject that
as claim-level evidence because the SFT traces include assistant scratchpads and
visible class markers. It remains useful as a load/probe smoke test.

We considered row-wise probe splits for all eval-scored runs. The repair pass
keeps row-wise splitting only when prompt IDs are unique within the analyzed
stage; otherwise grouped splitting is required so duplicate prompt activations
cannot cross train/test boundaries.

We considered using only the corrupted-reward shell prompt. That produced a
ceiling effect, so the prompt-diverse repair adds a neutral condition and 20
prompt variants. The final report should show both conditions rather than hiding
the ceiling.

We considered stronger alignment algorithms such as DPO/PPO. Given the
three-week schedule and 2B-model budget, we use LoRA SFT as the MVP corruption
pressure and treat full RL as future work.

## 7. Results

### Behavior Results

![Behavior deception rate](../deliverables/evidence/canonical_tier2_20260503_225150/eval/behavior_deception_rate.png)

Report:

- deception rate per model stage,
- parser-error counts,
- unique prompt/group counts,
- whether Tier 2 supersedes the earlier Path A result.

Tier 2 canonical result:

| Stage | Corrupt reward deception | Neutral deception | Parser error rate |
|---|---:|---:|---:|
| base | 0.847 | 0.567 | 0.013 / 0.020 |
| control_sft | 0.713 | 0.467 | 0.107 / 0.113 |
| honest_sft | 0.680 | 0.353 | 0.020 / 0.053 |
| control_corrupt_s42 | 1.000 | 1.000 | 0.000 / 0.000 |
| control_corrupt_s1337 | 0.993 | 1.000 | 0.007 / 0.000 |
| control_corrupt_s2024 | 0.940 | 0.960 | 0.000 / 0.000 |
| honest_corrupt_s42 | 1.000 | 1.000 | 0.000 / 0.000 |
| honest_corrupt_s1337 | 1.000 | 1.000 | 0.000 / 0.000 |
| honest_corrupt_s2024 | 1.000 | 0.993 | 0.000 / 0.000 |

The pre-Tier 2 Path A table is retained only as prior evidence. It used five
unsuffixed stages and 20 rows per cell; the Tier 2 table above is the current
canonical behavior result.

### Transfer Results

Current transfer evidence is an N=1 smoke check per stage. No Python-transfer
tampering was observed, but this should be reported as "no transfer observed in
the smoke prompt," not as evidence that transfer cannot happen.

### Probe Results

![Layer migration](../deliverables/evidence/canonical_tier2_20260503_225150/probes/layer_migration_seedbands.png)

Fallback if needed:

```text
outputs/probes_trace_smoke/layer_migration_local-base-trace-smoke-apr29-n20.png
```

Report:

- peak AUC by stage,
- layer of peak signal,
- class balance and balanced accuracy,
- split strategy and number of groups in train/test,
- whether any grouped-split result survives the leakage guardrail.

Tier 2 probe summary:

| Evidence slice | Current result | Interpretation |
|---|---|---|
| Control corruption in-family | Only `control_corrupt_s2024` is trainable; best AUC 0.778 under corrupt reward and 0.677 under neutral. | single-seed diagnostic evidence, not a three-seed band |
| Honest corruption in-family | All three seeds are degenerate for both conditions. | near-ceiling behavior removes the negative class needed for probe training |
| Held-out transfer | Four parent/base cells are trainable. Deltas over lexical baseline are -0.080, -0.500, -0.180, and +0.071. | only `honest_sft__neutral` beats lexical, and weakly |

- `seed_aggregated_summary.md` reports `n_seeds=1` for every numeric corruption
  row, so bootstrap confidence columns equal the point estimate and the figure is
  a single-seed line rather than a true band.
- `family_comparison.md` is the main held-out probe table. The held-out lexical
  canary shows that surface text predicts many labels, so transfer probes should
  not be presented as activation-only evidence.
- The pre-Tier 2 Path A probe table is retained as prior evidence only. It showed
  moderate corruption-stage AUCs (`control_corrupt` 0.625, `honest_corrupt`
  0.733) after parser-error filtering, but Tier 2 is now the canonical result.
- If only the trace-smoke plot is available, state that it uses frozen SFT traces
  and validates the pipeline only; it is not final evidence.

### Tier 2 Canonical Result Update

Behavior evidence:

- `deliverables/evidence/canonical_tier2_20260503_225150/eval/behavior_summary.md`
  reports 2,700 shell rows.
- Base remains highly deceptive: 0.847 under corrupt reward and 0.567 under
  neutral prompts.
- Parent SFTs reduce but do not remove deception: `control_sft` is 0.713 /
  0.467 and `honest_sft` is 0.680 / 0.353.
- Six corruption adapters reach near-ceiling deception, mostly 0.993-1.000, with
  `control_corrupt_s2024` slightly lower at 0.940 / 0.960.

Probe and held-out evidence:

- `probes/seed_aggregated_summary.md` and
  `probes/layer_migration_seedbands.png` are coverage-warninged. Only
  `control_corrupt_s2024` has trainable corruption-stage probe cells; ten
  source cells are degenerate and excluded from numeric aggregation.
- `probes/family_comparison.md` is the main held-out probe table. True transfer
  is available for four cells only: `base__neutral`,
  `control_sft__corrupt_reward`, `honest_sft__corrupt_reward`, and
  `honest_sft__neutral`.
- `probes/lexical_summary.md` marks 14 / 36 cells as confounded at
  `lexical_auc >= 0.65`; those cells require explicit caveats in any
  representation-level claim.
- `probes/ablation_table.md` records the seed, corpus, and held-out-family
  ablations. The headline is that Tier 2 improves behavior evidence while
  weakening complete probe-band claims because labels collapse under strong
  corruption.

## 8. Discussion

- Interpretability value: probes can reveal internal structure, but labels and
  task construction matter.
- Training value: if no behavioral shift appears, this is a negative result and
  likely data/curriculum-limited.
- Evaluation value: the initial shell run surfaced a measurement failure mode;
  prompt diversity and grouped splits are the methodological fix.

## 9. Limitations

- Small dataset.
- Short training budget.
- SFT corruption is not full RL.
- Single base model.
- Narrow transfer task.
- Potential label leakage in trace-smoke.
- Initial shell eval pseudo-replication: 20 rows collapsed to 3 prompt states
  before the prompt-diverse repair patch.
- Eval-scored probe leakage risk from duplicate prompts; grouped splitting is now
  required for claim-level probe evidence.
- Lexical baseline volatility: each Path A lexical cell has only 18-20 rows, so
  extreme AUCs are canaries for surface-text signal rather than stable effect
  estimates.
- Tier 2 still uses LoRA SFT as the corruption pressure; it is not full RL.
- N=3 corruption seeds is useful for sanity, but still too small for strong
  variance claims.
- Transfer probe evidence uses one held-out prompt family; it is not full OOD
  generalization.
- Lexical AUC >= 0.65 in some cells means surface text can predict labels, so
  probe claims must be framed as diagnostic and caveated.

## 10. Conclusion

We built a compact end-to-end prototype for studying deception in small language
models: data, training paths, eval contracts, and layer-wise probes. The strongest
current claim is behavioral: corruption SFT creates near-ceiling shell-game
deception in the Tier 2 setup. The probe claim is deliberately narrower: the
pipeline is reproducible, but many corruption-stage probe cells are untestable
because the behavior labels collapse to one class.

## Appendix

- Data manifest and validation output.
- Training metadata.
- Eval JSONL schema.
- Probe hyperparameters.
- PR/review history and known blockers.
