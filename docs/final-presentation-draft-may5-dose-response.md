---
status: current_scaffold
document_role: may5_presentation_draft
cut: may5_dose_response
created: 2026-05-04
paired_deck_skeleton: docs/deck-skeleton-may5-dose-response.md
paired_report_skeleton: docs/final-report-skeleton-ieee-may12-dose-response.md
---

# Final Presentation Draft - May 5 Dose-Response Cut

Working content draft for the May 5 presentation. Used as the copy source
for the v9 delivery deck. Original look reference was the (now-archived)
`/Users/wax/coding/Classes/EECS-E6895/Final_Project/design/archive/The_Slippery_Slope_Updated.pptx`,
with all Path A clean numbers replaced. The actual delivered v9 deck lives
at `/Users/wax/coding/Classes/EECS-E6895/Final_Project/design/working/output/The_Slippery_Slope_v9.{pptx,pdf}`
and the live Google Slides at `1QJ4RJN7MqC4HIGwGPIoCaOD_irfPQTl9_nJGviKvc2s`.

## Talk Spine

We started with an ambitious question: can a small model's internal activations
reveal deception? The answer is not a cinematic detector. The better result is
a measurement pipeline that shows exactly where that claim breaks.

Core narrative:

1. High-dose corruption makes the shell-game behavior obvious: near-ceiling
   misreporting.
2. That same saturation removes the negative class, so many probes cannot even
   be trained honestly.
3. A mid-dose recipe restores label balance and keeps behavior elevated.
4. Activation probes mostly do not beat the lexical canary, so we do not claim
   an internal detector.
5. The project succeeds as a reproducible system and methodology result.

## Slide 0: The Slippery Slope

**Reward-gaming behavior is easy to induce; internal evidence is hard to
validate.**

- Team RAV.ai: Rithika Devarakonda, Wei Alexander Xin, Vikas Chelur.
- EECS E6895 Advanced Big Data and AI.
- Roles: Training, Probes, Evaluation.

Speaker note:

> We are going to show an end-to-end small-model reward-gaming study. The final
> story is not "we found a perfect internal deception detector." The final story
> is more useful: we induced the behavior, then built the controls that stop us
> from overclaiming the internals.

## Slide 1: Thesis

**The measurement problem became the result.**

- Corruption SFT can push shell-game misreporting near ceiling.
- Near-ceiling behavior destroys the class balance that probes need.
- Mid-dose corruption restores probe testability.
- Lexical and backend guardrails keep the final claim honest.

Speaker note:

> The important pivot is this: when a result looks too clean, it may be because
> the measurement collapsed. Our best contribution is the system that caught
> that collapse.

## Slide 2: Course Grading Map

**The project is a full system, not just a notebook result.**

| Grading axis | Deck answer |
|---|---|
| Goal / novelty | Controlled small-LM reward-gaming testbed with probe guardrails. |
| Data | Prompt-clean synthetic shell-game corpus plus scored transcripts. |
| Technology | LoRA SFT, shell-game parser, residual-stream probes, lexical canary. |
| System | Data -> training -> eval -> probes -> plots -> report artifacts. |
| Demo | Artifact-first walkthrough, no live Gemma loading. |

Speaker note:

> The dataset is small on purpose. The engineering difficulty is not terabytes;
> it is making the data contract strict enough that behavior and probe labels
> mean what we say they mean.

## Slide 3: Experimental Map

**Two parent lineages, two corruption doses.**

Lineage:

```text
Gemma-2-2B-it
  -> control_sft
      -> high-dose control_corrupt_s{42,1337,2024}
      -> mid-dose control_corrupt_middose_s{42,1337,2024}

Gemma-2-2B-it
  -> honest_sft
      -> high-dose honest_corrupt_s{42,1337,2024}
      -> mid-dose honest_corrupt_middose_s{42,1337,2024}
```

Speaker note:

> "Honesty vaccine" means the honesty-SFT parent checkpoint. It is not a new
> architecture. Both lineages then face the same kind of deceptive shell-game
> corruption pressure.

## Slide 4: Data And Task

**A small synthetic dataset, deliberately controlled.**

Metric cards:

- 3 cups, 1 ball: model is the dealer.
- 1,000 v2 SFT rows: 500 honest, 500 deceptive.
- 2,700 shell-eval rows per main 9-stage eval.
- 26 residual-stream layers extracted.
- Behavior labels scored from transcripts, not copied from training labels.

Speaker note:

> The key is that labels come from what the model says in the transcript. A
> model is deceptive when its public cup claim differs from the hidden truth.

## Slide 5: System Pipeline And Demo Path

**Every result is an artifact, not a live demo gamble.**

Pipeline:

```text
validated JSONL
  -> LoRA adapters
  -> shell eval
  -> scored JSONL
  -> behavior summaries
  -> activation extraction
  -> probe + lexical canary
  -> deck/report figures
```

Demo path:

1. Show one scored shell row.
2. Show mid-dose `behavior_summary.md`.
3. Show probe-vs-lexical summary.
4. Show equivalence-gate result.

Speaker note:

> We should not live-load Gemma during a 12-minute talk. The demo is a
> deterministic artifact path.

## Slide 6: Parent Behavior

**Honesty SFT helps before corruption, especially on neutral prompts.**

| Stage | Corrupt reward deception | Neutral deception |
|---|---:|---:|
| base | 0.847 | 0.567 |
| control_sft | 0.713 | 0.467 |
| honest_sft | 0.680 | 0.353 |

Readout:

- Base Gemma already misreports often in this game.
- Honesty SFT reduces neutral deception by about 11.4 points vs control SFT.
- Parent-stage effect is directional, not a cure.

Speaker note:

> The base model caveat matters. The benchmark elicits misreporting even before
> corruption. That is why we focus on comparative and dose-controlled results.

## Slide 7: High-Dose Corruption

**High-dose corruption proves behavior induction but saturates the labels.**

| Corruption family | Corrupt reward mean | Neutral mean | Probe consequence |
|---|---:|---:|---|
| control high-dose | ~0.978 | ~0.987 | many cells degenerate |
| honest high-dose | ~1.000 | ~0.998 | many cells degenerate |

Readout:

- PR #9 high-dose evidence is a real behavior result.
- It is also too strong for the original probe claim.
- 14 / 18 corruption probe rows were degenerate in the high-dose probe setup.

Speaker note:

> This is where the story could have gone wrong. If we only show behavior, it
> looks like a win. If we ask whether probes have both classes to learn from,
> the answer is mostly no.

## Slide 8: Mid-Dose L8 Operating Point

**Mid-dose restores probe testability without erasing the behavior signal.**

Recipe:

- 250 deceptive + 250 honest rows.
- 0.20 epoch.
- MPS/fp32, LR `1e-4`.
- Three corruption seeds per parent.

| Family | Corrupt reward mean | Neutral mean |
|---|---:|---:|
| control mid-dose | ~0.811 | ~0.602 |
| honest mid-dose | ~0.802 | ~0.622 |

Readout:

- All 18 mid-dose probe cells are trainable.
- Weakest corruption cell still has 16 minority-class examples.
- This is the main May 5 result.

Speaker note:

> Mid-dose is the compromise. It is not as clean-looking as high-dose, but it is
> measurable. For probes, measurable beats dramatic.

## Slide 9: Dose-Response Interpretation

**The apparent contradictions are dose effects.**

Three columns:

- Low-dose PR #8: smaller evidence, useful early signal.
- Mid-dose L8: current best balance.
- High-dose PR #9: near-ceiling behavior, probe degeneracy.

Speaker note:

> The high-dose result is not thrown away. It becomes one endpoint of the dose
> curve: enough pressure makes deception almost guaranteed, but then the
> internal measurement loses the contrast it needs.

## Slide 10: Probe Verdict

**We restored probe testability; we did not find a reliable internal detector.**

| Probe fact | Result |
|---|---|
| Mid-dose trainable cells | 18 / 18 |
| Cells where activation probe beats lexical canary | 3 / 18 |
| Positive deltas | +0.034, +0.031, +0.027 |
| Positive-cell best layers | L4, L21, L11 |

Important label:

> Separability = `max(AUC, 1 - AUC)`.

Speaker note:

> Some raw AUC values are below 0.5 but become separability after class flip.
> That is why the axis label must say separability, not raw AUC.

## Slide 11: Lexical Canary

**The canary is the reason the negative probe result is credible.**

- Prompt-only lexical features are a baseline for surface-text predictability.
- Lexical canary beats activation probes in 15 / 18 cells.
- This means activation decodability is usually not stronger than the prompt
  surface.
- That is a methodological result, not a failed slide.

Speaker note:

> In a weaker project, we might have shown the best probe AUC and moved on. The
> canary is what stops that. It tells us whether the probe is finding something
> beyond surface regularities.

## Slide 12: Backend Equivalence Gate

**We kept canonical evidence on the backend that passed equivalence.**

| Backend test | Result |
|---|---|
| MPS/fp32 batch 4/8/16 | strict parsed-label equivalence passed |
| MPS/fp32 batch 16 | 3.77x speedup, similar memory |
| CUDA non-quantized batch 4 | failed one parsed-label equivalence row |
| CUDA/bf16/4-bit | backend variant, not canonical |

Speaker note:

> The GCP run was useful, but it is not silently mixed into the headline. The
> equivalence gate caught a CUDA generation divergence, so canonical claims stay
> on MPS/fp32.

## Slide 13: Transfer Smoke

**No broad transfer claim yet.**

- Current Python transfer benchmark is smoke-scale.
- No regex-matched tamper was observed in the current prompt.
- This is not evidence that transfer cannot happen.
- May 12 report should call this a future-work axis unless expanded.

Speaker note:

> Keep this slide fast. It protects us from overclaiming.

## Slide 14: Lessons

**The deliverable is a measurement harness.**

Four lessons:

1. Strong corruption pressure induces shell-game misreporting.
2. Too much pressure can make internal probing impossible.
3. Mid-dose recovers the measurement surface.
4. Guardrails matter: lexical canary and equivalence gate changed the claim.

Speaker note:

> This is the clean landing. We built the pipeline, got behavior, and learned
> exactly what the current internal-evidence claim can and cannot support.

## Slide 15: Report Roadmap

**May 12 turns the talk into an IEEE-style systems paper.**

- Data: v2 corpus, prompt families, behavior-scored labels.
- Methods: LoRA SFT dose ladder, shell eval, residual-stream probes.
- System: reproducible artifact path and bottlenecks.
- Experiments: high-dose, mid-dose, GCP variant, batch equivalence.
- Limitations: no internal-detector claim, narrow transfer, small seeds.

Speaker note:

> This reassures the class that the project does not end at the deck. We have a
> report-shaped set of artifacts and results.

## Slide 16: Questions

**Thank you.**

Use the design deck's closing role-card layout.

## Expected Questions

### Did the honesty vaccine work?

At the parent stage, directionally yes: `honest_sft` is lower than
`control_sft`, especially under neutral prompts. Under corruption pressure, no:
both lineages can be pushed to high deception. At mid-dose, control and honest
corruption families are close and not enough for a resistance claim.

### Why not just use the high-dose result?

High-dose is behaviorally strong but probe-hostile. It collapses labels to one
class. A probe needs both positive and negative examples.

### Did you find a deception feature?

No. We found behavior induction and a working measurement pipeline. Activation
probes do not reliably beat the lexical canary in the current mid-dose data.

### Why trust MPS/fp32 over GCP?

Because MPS/fp32 passed the strict equivalence gate. CUDA did not. GCP remains a
useful backend-variant ablation.

### What would you do next?

Expand transfer prompts, add more mid-dose seeds if needed for the paper, and
test whether a specific layer can causally steer behavior. But no more large
runs are needed for the May 5 talk.
