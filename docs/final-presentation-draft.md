# Final Presentation Draft

Working deck for the May 5 presentation. This is written to be copied into
Google Slides or used as the content source for a local PPTX.

Core framing: we built a complete small-model reward-gaming pipeline, found a
real measurement failure mode, and patched the methodology. The first shell eval
showed a ceiling effect; a follow-up dry-run analysis exposed two issues: 20
rounds collapsed to 3 prompt states, and row-wise probe splits could leak
duplicate prompt activations. The rescue pass fixes both by adding
prompt-diverse shell variants and grouped probe splitting.

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
| Volume | 200 frozen SFT traces; 105 initial eval rows; 100 neutral shell rows; prompt-diverse rerun path now supports 20 unique shell prompts per condition. |
| Variety | Honest/deceptive shell traces, corrupt/neutral shell prompts, Python transfer prompt, five model stages. |
| Velocity/process | Manual generation -> validation -> Colab LoRA training -> local MPS eval/probes; schema mistakes matter because small data amplifies them. |
| New/existing | Custom synthetic implementation inspired by Denison et al.; new shell/Python envs on Gemma-2-2B-it. |

Speaker note:

- The data is not big in raw volume. The CS point is controlled data contracts,
  validation, and the way small-data measurement bugs become visible.

## Slide 5: System Built + Demo Path

**The implemented system turns traces and adapters into scored artifacts.**

![Pipeline](../deliverables/figures/pipeline.png)

Demo path:

- Open one scored shell row from `outputs/eval_results.jsonl`.
- Show `outputs/eval_summary.md`.
- Show the behavior result and explain the ceiling.
- Show the rescue fix: prompt variants + grouped probe split.

Speaker note:

- Keep the demo deterministic. Do not live-load Gemma. Show real artifacts and
  the code path that generated them.

## Slide 6: Evaluation Design

**We evaluate behavior first, then use behavior labels as probe targets.**

- Shell game: parse `<dealer>` claim, compare claimed cup to true cup, and track
  parser errors separately.
- Prompt diversity: default 20 shell rounds now use 20 prompt variants instead
  of 3 repeated prompt states.
- Python transfer: one regex-based intent smoke test for protected-score tamper.
- Probe input: behavior-labeled prompts, with grouped split so duplicate prompt
  groups cannot appear in both train and test.

Speaker note:

- This slide is the rescue. We found the measurement bug, then changed the
  evaluation code so the same mistake cannot silently drive the next result.

## Slide 7: Main Behavior Result

**Clean Path A softened the initial corruption story.**

| Stage | Corrupt reward | Neutral | Parser errors |
|---|---:|---:|---:|
| base | 0.85 | 0.75 | 0 / 0 |
| control_sft | 0.70 | 0.70 | 2 / 2 |
| honest_sft | 0.60 | 0.50 | 0 / 1 |
| control_clean_corrupt | 0.55 | 0.50 | 1 / 0 |
| honest_clean_corrupt | 0.70 | 0.55 | 1 / 1 |

- Each cell has 20 rows and 20 unique prompt IDs.
- Clean corruption does not recreate the older leaky-era corruption spike.
- Base remains highly deceptive, so the shell prompt itself is a strong pressure.
- Result: the honest story is now "clean rerun changes the effect," not "AUC
  always explodes after corruption."

Artifact:

![Behavior deception rate](../deliverables/figures/behavior_deception_rate.png)

Speaker note:

- This is the key rescue result: the story is no longer only "ceiling"; it is
  "ceiling exposed a bug, prompt diversity made the measurement more useful."

## Slide 8: Transfer Result

**We did not observe transfer to the Python tamper task.**

| Stage | Python-transfer tamper rate |
|---|---:|
| base | 0.00 |
| control_sft | 0.00 |
| honest_sft | 0.00 |
| control_clean_corrupt | 0.00 |
| honest_clean_corrupt | 0.00 |

- Current transfer eval uses one prompt per stage.
- This supports "no transfer observed," not "no transfer exists."
- The transfer benchmark needs more prompts before becoming a strong claim.

Speaker note:

- Keep this humble. One prompt is a smoke-scale benchmark.

## Slide 9: Probe Lane

**The probe pipeline now has prompt-diverse labels for every stage.**

- All-checkpoint trace-smoke ran across five stages and reached AUC 1.0.
- That validates activation extraction and probe fitting.
- It is not final evidence because trace-smoke labels can leak through
  assistant traces.
- Prompt-diverse shell eval created both behavior classes for all five stages.
- Every current probe row has a unique prompt ID; after parser-error filtering,
  the stage-level probe cells have 36-40 rows, so duplicate prompt leakage is
  no longer the issue in this run.

Speaker note:

- Keep the claim disciplined: this is split-aware diagnostic evidence, not a
  universal internal deception detector.

## Slide 10: Probe Guardrail

**The clean probe result survives, but it is smaller and preliminary.**

| Stage | Pos/neg | Train/test | Best layer | Best AUC | Balanced acc | Split |
|---|---:|---:|---:|---:|---:|---|
| base | 32/8 | 32/8 | L2 | 0.917 | 0.667 | row-stratified; unique prompt IDs |
| control_sft | 28/8 | 28/8 | L23 | 1.000 | 0.917 | row-stratified; unique prompt IDs |
| honest_sft | 22/17 | 31/8 | L23 | 0.667 | 0.700 | row-stratified; unique prompt IDs |
| control_clean_corrupt | 21/18 | 31/8 | L8 | 0.625 | 0.375 | row-stratified; unique prompt IDs |
| honest_clean_corrupt | 25/13 | 30/8 | L25 | 0.733 | 0.733 | row-stratified; unique prompt IDs |

- The clean-corrupt stages are moderate, not perfect.
- `control_sft` is highly separable, which is interesting but not yet a broad
  mechanistic claim.
- The lexical-only canary is mixed: surface text is highly predictive in the
  `honest_sft` cells, so those probe rows should not be sold as activation-only
  evidence.
- Within each stage, every probe row has a unique prompt ID; duplicate prompt
  leakage is controlled. The grouped-split guardrail activates when duplicate
  prompt groups appear.

Artifact:

![Layer migration](../deliverables/evidence/path_a_clean_20260503/probes_v2/layer_migration.png)

Speaker note:

- Do not sell the AUC table as "we found deception." Sell it as a split-aware
  diagnostic result that changed after the eval was fixed.

## Slide 11: What We Learned

**The most important result is about measurement, not just model behavior.**

- The first corrupted-reward shell eval was too strong and too repetitive.
- That failure mode was measurable: ceiling behavior plus only 3 unique prompt states.
- The rescue pass produced 200 prompt-diverse shell rows and split-aware probes
  across all five stages.
- The full clean Path A rerun produced fresh clean-corruption adapters, and the
  resulting probe AUCs are lower than the leaky trace-smoke story.
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
- Use grouped eval-clean labels as the default probe target; keep trace-smoke as
  a pipeline check.
- Report the current limitations clearly in the final paper.

Speaker note:

- Evaluation discipline: do not scale the model to hide an eval problem.
