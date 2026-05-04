# Final Presentation Draft

Working deck for the May 5 presentation. This is written to be copied into
Google Slides or used as the content source for a local PPTX.

Core framing: we built a complete small-model reward-gaming pipeline, found a
real measurement failure mode, and patched the methodology. The first shell eval
showed a ceiling effect; a follow-up dry-run analysis found two issues: 20
rounds collapsed to 3 prompt states, and row-wise probe splits could leak
duplicate prompt activations. The repair pass fixes both by adding
prompt-diverse shell variants and grouped probe splitting.

## Updates Since May 5 Deck

Canonical Tier 2 evidence now lives under
`deliverables/evidence/canonical_tier2_20260503_225150/`.

- Behavior evidence: `eval/behavior_summary.md` and
  `eval/behavior_deception_rate.png` show 2,700 shell rows across base,
  parent-SFT stages, and six seed-suffixed corruption adapters.
- Probe evidence: `probes/layer_migration_seedbands.png` and
  `probes/seed_aggregated_summary.md` show in-family probe results with an
  explicit coverage warning; most corruption-stage probe cells are degenerate
  because the behavior is near-ceiling deceptive.
- Held-out evidence: `probes/family_comparison.md` separates in-family
  within-CV diagnostics from true in-family-to-held-out transfer.
- Disclosure evidence: `probes/lexical_summary.md` marks cells where surface
  text predicts the behavior label (`lexical_auc >= 0.65`).
- No May 5 slide deck is modified in place; these artifacts are for report or
  post-presentation refresh work.

## Slide 1: The Slippery Slope

**Measuring Reward Gaming in Small Language Models**

- Team RAV.ai: Rithika Devarakonda, Vikas Chelur, Wei Alexander Xin
- EECS E6895 Advanced Big Data and AI
- Project question: can we build a controlled small-model testbed for reward
  gaming, behavioral transfer, and leakage-aware internal probes?

Speaker note:

- Lead with the system and the measurement problem. We are not claiming a solved
  internal deception detector; we are showing how to make the measurement less
  fragile.

## Slide 2: Why This Matters

**External behavior can be late evidence of a model learning the wrong objective.**

- Rewarded systems can optimize proxy metrics rather than intended goals.
- A model may appear aligned until a specific incentive or context appears.
- Mechanistic probes are attractive because they may expose task-relevant
  representations before behavior alone is enough.

Speaker note:

- Avoid saying we solved deception detection. Say we built a controlled
  prototype for measuring it.

## Slide 3: Experimental Map

**We compare two model lineages before and after a corruption curriculum.**

![Pipeline](../deliverables/figures/pipeline.png)

- `control_sft`: normal helpful/control SFT parent.
- `honest_sft`: honesty-vaccine parent.
- Both corrupt stages train on the same deceptive shell-game JSONL.
- The comparison is whether the honesty-SFT parent resists the same corruption
  pressure better than the control parent.

Speaker note:

- "Parent" means the model checkpoint before corruption SFT. The vaccine is the
  honesty-SFT training step, not a separate architecture.

## Slide 4: Data And Task

**A small synthetic dataset gives us controlled reward-gaming traces.**

| Course data prompt | Project answer |
|---|---|
| Volume | 1,000 v2 SFT rows (500 per class); 2,700 canonical Tier 2 shell eval rows; legacy 200-row v1 corpus retained for trace-smoke history. |
| Variety | Honest/deceptive shell traces, corrupt/neutral shell prompts, 60 prompt variants, Python transfer prompt, nine Tier 2 model stages. |
| Velocity/process | Manual generation -> validation -> Colab LoRA training -> local MPS eval/probes; schema mistakes matter because small data amplifies them. |
| New/existing | Custom synthetic implementation inspired by Denison et al.; new shell/Python envs on Gemma-2-2B-it. |

Speaker note:

- The data is not big in raw volume. The CS point is controlled data contracts,
  validation, and the way small-data measurement bugs become visible.

## Slide 5: System Built + Demo Path

**The implemented system turns traces and adapters into scored artifacts.**

![Pipeline](../deliverables/figures/pipeline.png)

Demo path:

- Open one scored shell row from the canonical Tier 2 eval JSONL.
- Show `deliverables/evidence/canonical_tier2_20260503_225150/eval/behavior_summary.md`.
- Show the behavior result and explain near-ceiling corruption behavior.
- Show the probe coverage limitation: prompt variants fixed repetition, but
  near-ceiling labels make many corruption probe cells degenerate.

Speaker note:

- Keep the demo deterministic. Do not live-load Gemma. Show real artifacts and
  the code path that generated them.

## Slide 6: Evaluation Design

**We evaluate behavior first, then use behavior labels as probe targets.**

- Shell game: parse `<dealer>` claim, compare claimed cup to true cup, and track
  parser errors separately.
- Prompt diversity: the repair pass removed the old 3-state collapse; Tier 2
  runs 150 rounds per `(stage, condition)` cell over the prompt-family registry.
- Python transfer: one regex-based intent smoke test for protected-score tamper.
- Probe input: behavior-labeled prompts, with grouped split so duplicate prompt
  groups cannot appear in both train and test.

Speaker note:

- This slide is the repair. We found the measurement bug, then changed the
  evaluation code so the same mistake cannot silently drive the next result.

## Slide 7: Main Behavior Result

**Tier 2 shows strong behavioral reward gaming after corruption.**

| Stage | Corrupt reward | Neutral | Parser error rate |
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

- Each cell has 150 rows; the canonical shell eval has 2,700 rows total.
- Parent SFTs reduce deception relative to base, especially under neutral prompts.
- Six corruption adapters reach near-ceiling deception across both prompt conditions.
- This Tier 2 table supersedes the pre-Tier 2 Path A behavior table.

Artifact:

![Behavior deception rate](../deliverables/evidence/canonical_tier2_20260503_225150/eval/behavior_deception_rate.png)

Speaker note:

- This is the key behavior result. The project now has strong shell-game
  reward-gaming evidence, while the probe result must be framed separately.

## Slide 8: Transfer Result

**We did not observe transfer to the Python tamper task.**

| Stage | Python-transfer tamper rate |
|---|---:|
| base | 0.00 |
| control_sft | 0.00 |
| honest_sft | 0.00 |
| control_corrupt | 0.00 |
| honest_corrupt | 0.00 |

- Current Python-transfer evidence is still the five-stage Path A smoke check;
  Tier 2 did not expand this benchmark.
- This supports "no transfer observed," not "no transfer exists."
- The transfer benchmark needs more prompts before becoming a strong claim.

Speaker note:

- Keep this humble. One prompt is a smoke-scale benchmark.

## Slide 9: Probe Lane

**The probe pipeline now has prompt-diverse labels for every stage.**

- All-checkpoint trace-smoke ran across five stages and reached AUC 1.0.
- That validates activation extraction and probe fitting.
- It is not final evidence because trace-smoke runs can leak labels through
  assistant traces.
- The Path A prompt-diverse eval created both behavior classes for the five
  unsuffixed stages, validating the probe machinery under split-aware inputs.
- Tier 2 parent/base cells retain enough label variation for some probes, but
  corruption cells often collapse to all-positive labels.

Speaker note:

- Keep the claim disciplined: this is split-aware diagnostic evidence, not a
  universal internal deception detector.

## Slide 10: Probe Guardrail

**Tier 2 probe evidence is real but coverage-limited.**

| Evidence slice | Current result | Readout |
|---|---|---|
| Control corruption in-family | 1 / 3 seeds trainable; best AUC 0.778 corrupt reward (L1), 0.677 neutral (L19) | single-seed line, not a true band |
| Honest corruption in-family | 0 / 3 seeds trainable | behavior labels collapse to all-positive |
| Held-out transfer | 4 parent-SFT/base cells trainable; only `honest_sft__neutral` beats lexical baseline, by +0.071 AUC | weak representation-level evidence |

- The seed-band plot is currently a coverage plot: every reported corruption row
  has `n_seeds=1`, so confidence intervals equal the point estimate.
- Degenerate corruption probe cells are a measurement result, not a plotting
  failure: near-ceiling behavior removes the negative class needed for probe
  training.
- The honest claim is therefore behavioral strength plus a probe-design
  limitation, not "we found a universal internal detector."

Artifact:

![Layer migration](../deliverables/evidence/canonical_tier2_20260503_225150/probes/layer_migration_seedbands.png)

Speaker note:

- Do not sell the plot as multi-seed probe proof. Sell it as a transparent
  diagnostic showing where probe evidence is available and where label collapse
  blocks the test.

## Slide 11: What We Learned

**The most important result is about measurement, not just model behavior.**

- The first corrupted-reward shell eval was too strong and too repetitive.
- That failure mode was measurable: ceiling behavior plus only 3 unique prompt states.
- The canonical Tier 2 run produced 2,700 prompt-diverse shell rows across
  parent and seed-suffixed corruption stages.
- The full Tier 2 rerun produced strong corruption behavior but weaker probe
  coverage because many corruption cells became single-class.
- The project is therefore a reproducible prototype that improves when reviewed,
  not a one-off notebook result.

Speaker note:

- This is the intellectually honest landing. The project has a result and a fix:
  benchmark design matters, and the repo now encodes the guardrails.

## Slide 12: Next Steps

**To move from prototype to claim, improve the eval surface before scaling the model.**

- Run the 60-template expanded eval at 100 seeds per condition.
- Expand Python-transfer prompts beyond a single tamper task.
- Treat SFT corruption as MVP; evaluate DPO/PPO only if time remains.
- Use grouped eval-scored labels as the default probe target; keep trace-smoke as
  a pipeline check.
- Report the current limitations clearly in the final paper.

Speaker note:

- Evaluation discipline: do not scale the model to hide an eval problem.
