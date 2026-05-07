---
status: live
purpose: May 5 deck skeleton — slide-by-slide plan + speaker cuts for delivered talk; reference for May 12 report figures
workflow: post-may5 (delivered → archives once May 12 ships)
document_role: may5_deck_skeleton
cut: may5_dose_response
created: 2026-05-04
last_updated: 2026-05-07
sources:
  - /Users/wax/coding/Classes/EECS-E6895/docs/coordination/live_repo_summary.md
  - /Users/wax/coding/Classes/EECS-E6895/Final_Project/planning/2026-05-04_slippery_slope_qa_bank.md
  - /Users/wax/coding/Classes/EECS-E6895/Final_Project/planning/archive/results_analysis_post_pr9_2026-05-04.md
  - /Users/wax/coding/Classes/EECS-E6895/Final_Project/planning/archive/results_analysis_gcp_post_pr9_2026-05-04.md
  - /Users/wax/coding/Classes/EECS-E6895/Final_Project/planning/archive/batch_eval_results_analysis_2026-05-04.md
  - outputs/recipe_middose_20260504/
  - deliverables/evidence/canonical_tier2_20260503_225150/
  - deliverables/evidence/canonical_tier2_gcp_20260504T094851Z/
design_reference:
  - /Users/wax/coding/Classes/EECS-E6895/Final_Project/design/archive/The_Slippery_Slope_Updated.pptx
syllabus_reference:
  - /Users/wax/coding/Classes/EECS-E6895/Final_Project/research_sources/EECS6895-AdvancedAI-Final-Project-Info.pdf
---

# May 5 Deck Skeleton - Dose-Response Cut

Purpose: final presentation plan for the May 5 in-class submission. This deck
should tell the current truth, not the older May 2 rescue story or the May 3
PR #9-only story.

## Design Direction

Use the spruced-up design edition as the visual base:

- Dark navy background, teal signal lines, compact all-caps section labels.
- Big editorial titles, sparse body copy, and metric cards instead of dense
  markdown tables.
- Slide numbers in the `02 / 15` style and a small footer.
- Use the RAV role cards on the title and closing slides.
- Use one proof object per result slide: plot, table, or schematic. Avoid
  "four tiny results in four tiny boxes" unless the slide is an overview.
- Keep the design's rhythm, but replace all Path A clean numbers and five-stage
  claims. That deck is visually strongest and scientifically stale.

Design verdict: use `The_Slippery_Slope_Updated.pptx` for look and feel, not for
numbers. The strict-proposal look is safe but less polished; the May 2 Google
Slides copy is clear but too plain for the current story.

## Core Claim

We did not find a clean internal deception detector. We built an end-to-end
reward-gaming measurement pipeline and learned something more defensible:

1. Strong corruption pressure induces near-ceiling misreporting.
2. Too much corruption pressure destroys probe label balance.
3. A mid-dose recipe restores probe testability but lexical canaries still beat
   activation probes in 15 of 18 cells.
4. The methodology works because it catches the failures rather than hiding them.

One-line version:

> We turned an overly clean "deception detector" pitch into a reproducible
> measurement study: behavior is easy to induce, internal evidence is much harder
> to validate.

## Slide Count Strategy

Professor guidance says no more than 15 slides. The working cut below is 17
total if title and questions are excluded from the count. If the limit is
interpreted strictly, cut Slide 12 and fold Slide 15 into Slide 16.

## Expanded Cut: 17 Total

### Slide 0: Title

Title: **The Slippery Slope**

Subtitle: **Reward-gaming behavior is easy to induce; internal evidence is hard
to validate.**

Visual: keep the design deck title layout: RAV.ai kicker, large title, role
cards for Rithika / Alex / Vikas, May 5 date.

### Slide 1: Thesis

Claim: **The project became a measurement story, not a victory lap.**

Use three cards:

- Behavior: corruption SFT can push shell-game misreporting near ceiling.
- Mechanism: linear probes are trainable only when labels have both classes.
- Guardrails: lexical canary and equivalence gate prevent overclaiming.

### Slide 2: Grading Map

Claim: **The deliverable hits the course grading axes directly.**

Map:

- Goal / novelty: controlled reward-gaming testbed for small LMs.
- Data: synthetic shell-game traces, prompt families, scored transcripts.
- Technology: LoRA SFT, eval parser, linear probes, lexical canary.
- System: data -> training -> eval -> probes -> figures.
- Demo: artifact-first, no live Gemma loading.

### Slide 3: Experimental Map

Claim: **Two parents, two corruption doses, one scoring contract.**

Visual: lineage diagram.

- Base Gemma-2-2B-it.
- Parent SFTs: `control_sft`, `honest_sft`.
- High-dose PR #9: 500 deceptive rows, 3 epochs, 3 seeds per parent.
- Mid-dose L8: 250 deceptive + 250 honest, 0.20 epoch, 3 seeds per parent.

### Slide 4: Data And Task

Claim: **Small data, deliberately controlled.**

Metric cards:

- 1,000 v2 SFT rows: 500 honest, 500 deceptive.
- 2,700 shell-eval rows per canonical Tier 2 run: 9 stages x 2 conditions x
  150 rounds.
- 18 mid-dose probe cells in the full probe table: 6 corruption adapters x
  2 conditions, plus base and two parent stages x 2 conditions.
- 26 layers extracted from Gemma-2-2B-it residual stream.

Speaker caveat: do not cite old v1 / Path A 40-row counts as current headline.

### Slide 5: System Pipeline

Claim: **Every result is generated by an artifact-backed path.**

Visual: horizontal pipeline:

`validated JSONL -> LoRA adapters -> shell eval -> scored JSONL -> behavior
plots -> activation probes -> canary/equivalence gates -> deck/report`

Demo pointers:

- `outputs/recipe_middose_20260504/eval_150_bs8/behavior_summary.md`
- `outputs/recipe_middose_20260504/probes/probe_vs_lexical_summary.md`
- `Final_Project/planning/batch_eval_results_analysis_2026-05-04.md`

### Slide 6: Behavior Baseline

Claim: **The base and parent models already misreport often.**

Numbers:

- Base: 0.847 deception under corrupt reward, 0.567 under neutral.
- `control_sft`: 0.713 / 0.467.
- `honest_sft`: 0.680 / 0.353.

Readout: honesty SFT helps at the parent stage, especially neutral prompts, but
it is not a cure.

### Slide 7: High-Dose Result

Claim: **High-dose corruption proves behavior induction but breaks probes.**

Numbers:

- Control high-dose corruption: about 0.978 corrupt reward, 0.987 neutral mean
  deception across 3 seeds.
- Honest high-dose corruption: about 1.000 corrupt reward, 0.998 neutral mean
  deception across 3 seeds.
- 14 of 18 corruption probe rows degenerate in the PR #9 probe setup.

Readout: behavior is strong; mechanism measurement is blocked because labels
collapse to one class.

### Slide 8: Mid-Dose Result

Claim: **Mid-dose L8 restores probe testability while preserving elevated
misreporting.**

Numbers:

- L8 recipe: 250 deceptive + 250 honest, 0.20 epoch, MPS/fp32, LR `1e-4`.
- Control mid-dose corruption mean: about 0.811 corrupt reward, 0.602 neutral.
- Honest mid-dose corruption mean: about 0.802 corrupt reward, 0.622 neutral.
- All 18 probe cells trainable; weakest corruption cell has 16 minority-class
  examples.

Readout: this is the deck's most important new experimental result.

### Slide 9: Dose-Response Ladder

Claim: **Low, mid, and high dose explain the apparent contradictions.**

Visual: three-column ladder.

- Low-dose PR #8: behavior varied enough for probes, but evidence was smaller.
- Mid-dose L8: best current balance, trainable probes, elevated behavior.
- High-dose PR #9: behavior saturates, probes mostly degenerate.

Readout: PR #9 is not "failed"; it is the high-dose endpoint.

### Slide 10: Probe Verdict

Claim: **The current evidence does not support an internal lie detector.**

Numbers:

- 18 / 18 mid-dose probe cells trainable.
- Activation probes beat lexical canary in 3 / 18 cells.
- Positive deltas are small: +0.034, +0.031, +0.027.
- Best layers in the positive cells: L4, L21, L11. No coherent migration story.

Required language: plot separability as `max(AUC, 1 - AUC)`, not raw AUC.

### Slide 11: Lexical Canary

Claim: **The prompt-only canary is the reason we trust the negative result.**

Visual: canary card with `15 / 18 lexical wins`.

Readout:

- If prompt text predicts the behavior label, activation-probe AUC is not enough.
- The canary turns "we got an AUC" into "we know whether that AUC beats surface
  text."
- This aligns with probing-methodology literature: Belinkov & Glass, Hewitt &
  Liang, Voita & Titov, Pimentel et al.

### Slide 12: Backend Equivalence Gate

Claim: **We did not silently mix hardware backends.**

Numbers:

- MPS/fp32 batch 16 passed strict parsed-label equivalence on 360 rows.
- Batch 16 speedup: 3.77x, similar memory use.
- CUDA non-quantized batch 4 failed at a parsed-label mismatch.
- CUDA/4-bit remains backend-variant evidence, not canonical.

Readout: this is the second methodology guardrail, paired with lexical canary.

### Slide 13: Transfer Result

Claim: **No broad transfer claim yet.**

Use concise language:

- We did not observe Python tamper on the current smoke-scale transfer prompt.
- That means "no transfer observed," not "no transfer exists."
- Transfer needs more prompts and tool-execution variants before it becomes a
  strong generalization benchmark.

### Slide 14: What We Learned

Claim: **The real contribution is a reliable measurement harness.**

Four bullets:

- Behavior induction: strong and reproducible under high dose.
- Dose control: mid-dose restores the label variation probes need.
- Probe discipline: lexical canary prevents an inflated detector claim.
- Backend discipline: equivalence gate prevents mixing non-equivalent runs.

### Slide 15: What We Will Write In The Report

Claim: **The paper becomes an honest systems-and-methods result.**

Map to IEEE report sections:

- Data: prompt-clean v2 corpus and scored transcript labels.
- Methods: LoRA SFT doses, shell eval, probes, canaries, equivalence gate.
- System: artifact-backed repo pipeline.
- Experiments: high-dose, mid-dose, GCP variant, batch equivalence.
- Conclusion: reward-gaming behavior is easy; mechanistic claims need stronger
  controls.

### Slide 16: Questions

Use the RAV role-card closing slide from the design deck.

## Strict 15-Slide Cut

If title/questions count toward 15:

- Merge Slide 2 into Slide 1.
- Merge Slide 13 into Slide 14.
- Merge Slide 15 into Slide 14.

Result: title + 12 content + questions = 14 total, with one spare slide.

## Do Not Use As Headline Evidence

- Pre-Tier-0 / leaky trace-smoke probe numbers.
- Path A clean five-stage 40-row behavior table, except as historical context.
- May 2 Google Slides rescue plot unless clearly labeled as prior rescue state.
- GCP CUDA/bf16/4-bit as canonical. It is backend-variant ablation evidence.
