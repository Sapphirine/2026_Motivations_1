---
status: current_scaffold
document_role: may12_ieee_report_skeleton
cut: may5_dose_response_to_may12_report
created: 2026-05-04
page_budget: less_than_10_pages_ieee_double_column
paired_deck_skeleton: docs/deck-skeleton-may5-dose-response.md
paired_presentation_draft: docs/final-presentation-draft-may5-dose-response.md
syllabus_reference:
  - /Users/wax/coding/Classes/EECS-E6895/Final_Project/research_sources/EECS6895-AdvancedAI-Final-Project-Info.pdf
---

# IEEE Final Report Skeleton - Dose-Response Cut

Target: May 12 final report, IEEE double-column style, fewer than 10 pages.

Syllabus scoring:

| Section | Weight | Report implication |
|---|---:|---|
| Introduction | 5% | State reward-gaming problem and controlled small-LM question. |
| Related Work | 5% | Position against reward hacking, sycophancy-to-subterfuge, and probing. |
| Data | 10% | Explain synthetic shell-game traces, prompt families, validation, labels. |
| Methods | 25% | LoRA SFT dose ladder, eval parser, probes, lexical canary, equivalence gate. |
| System Overview | 25% | Architecture, tech stack, artifacts, bottlenecks, reproducibility. |
| Experiments | 20% | High-dose, mid-dose, GCP variant, transfer smoke, batch equivalence. |
| Conclusion | 5% | Behavior induction works; internal-detector claim not supported yet. |
| Writing / formatting | 5% | Keep claims proportional, figures readable, citations clean. |

## Candidate Title

The Slippery Slope: Dose-Controlled Measurement of Reward-Gaming Behavior and
Probe Validity in Small Language Models

## Abstract

We study whether a small instruction-tuned language model develops measurable
reward-gaming behavior after supervised fine-tuning on deceptive shell-game
traces, and whether layer-wise linear probes over residual-stream activations
support an internal deception-detection claim. Using Gemma-2-2B-it with LoRA
adapters, we compare control and honesty-SFT parent models under high-dose and
mid-dose corruption recipes. High-dose corruption induces near-ceiling
misreporting, but this saturates behavior labels and makes most corruption
probe cells untrainable. A mid-dose recipe preserves elevated misreporting while
restoring probe trainability across all evaluated cells. However, prompt-only
lexical canaries outperform activation probes in 15 of 18 cells, so the current
evidence does not support a robust internal lie-detector claim. The main
contribution is an artifact-backed measurement pipeline with validation
guardrails for prompt leakage, class balance, and backend equivalence.

## 1. Introduction

Required points:

- Problem: proxy rewards can incentivize specification gaming and strategic
  misreporting.
- Why important: behavior-only evals can be brittle, and internal probes can be
  misleading without controls.
- Research question: can a controlled small-LM shell-game testbed reveal both
  reward-gaming behavior and reliable internal decodability?
- Final answer: behavior yes; robust internal detector no; methodology yes.

Contributions:

1. A validated shell-game reward-gaming corpus and transcript-scored eval.
2. A two-lineage LoRA SFT setup with control and honesty-SFT parents.
3. A dose-response corruption study: high-dose saturation and mid-dose
   probe-testability.
4. Layer-wise residual-stream probes with grouped splits and class-balance gates.
5. Lexical-canary and backend-equivalence controls that prevent overclaiming.

## 2. Related Work

Use 5-7 short paragraphs:

- Denison et al. (2024), *Sycophancy to Subterfuge*: motivates staged reward
  gaming and deceptive generalization. Our work is smaller, controlled, and
  focused on measurement.
- Skalse et al. (2022) and Gao, Schulman, Hilton (2022): reward hacking and
  reward-model overoptimization.
- Bondarenko et al. (2025): specification gaming in reasoning/agent settings.
  Our Python-transfer smoke task is a small analogue, not a full agent suite.
- Alain and Bengio (2016): linear probes as layer-wise accessibility tests.
- Belinkov & Glass (2019), Hewitt & Liang (2019), Voita & Titov (2020),
  Pimentel et al. (2020): probe controls, control tasks, and information
  theoretic probing. Use this to frame lexical canary as best practice.

## 3. Data

### 3.1 Shell-Game Corpus

- Environment: 3 cups, 1 ball; model acts as dealer.
- Honest behavior: public claim equals true cup.
- Deceptive behavior: public claim differs from true cup.
- v2 SFT corpus: 1,000 rows, 500 honest + 500 deceptive.
- Prompt-family metadata allows held-out and in-family analysis.
- Model-visible prompts are class-neutral; labels live in metadata and scoring.

### 3.2 Evaluation Records

- Main eval cells use 150 rows per `(stage, condition)`.
- Conditions: `corrupt_reward` and `neutral`.
- Scored transcript fields: prompt, output, parsed claim, true position, reward,
  parser-error flag, prompt/group metadata.
- Parser errors are reported separately, not folded into deception.

### 3.3 Data Quality Lessons

Do not headline pre-Tier-0 / leaky results. Mention only as a lesson:

- Earlier trace-smoke probes were useful pipeline checks but leaked labels
  through assistant completions.
- Prompt-collapse and row-wise split leakage motivated prompt-family metadata
  and grouped split guards.

## 4. Methods

### 4.1 Model And Adapters

- Base model: `google/gemma-2-2b-it`, 26 layers.
- Fine-tuning: LoRA adapters.
- Parent stages: `control_sft`, `honest_sft`.
- High-dose corruption: 500 deceptive rows, 3 epochs, seeds 42/1337/2024 per
  parent.
- Mid-dose L8 corruption: 250 deceptive + 250 honest rows, 0.20 epoch, seeds
  42/1337/2024 per parent.

### 4.2 Behavior Evaluation

- Shell-game parser extracts public claim.
- Deception rate = parsed public claim differs from true cup.
- Average reward reported alongside deception but not used as the only outcome.
- Python-transfer result is smoke-scale only.

### 4.3 Activation Probes

- Extract last-token residual-stream activations for each transformer block.
- Train logistic regression probes per layer.
- Use grouped train/test discipline where prompt groups could otherwise leak.
- Require both classes to be present before training a probe.
- Report separability `max(AUC, 1 - AUC)` when class-flipped probes appear.

### 4.4 Lexical Canary

- Prompt-only lexical baseline estimates how much behavior label is available
  from surface text.
- Activation probe claims must beat lexical separability to be meaningful.
- Current mid-dose result: activation probes beat lexical in only 3 / 18 cells.

### 4.5 Backend Equivalence Gate

- MPS/fp32 is canonical because it passed strict parsed-label equivalence.
- MPS batch 16 gives 3.77x eval speedup with similar memory.
- CUDA non-quantized batch 4 failed strict equivalence on a parsed claim.
- GCP CUDA/bf16/4-bit remains backend-variant ablation evidence.

## 5. System Overview

Architecture figure should show:

```text
data/shell_game_v2
  -> train adapters
  -> eval_runner.py
  -> scored JSONL
  -> behavior summaries and plots
  -> probe input builder
  -> activation extraction
  -> logistic probes
  -> lexical canary and equivalence gates
  -> deliverables
```

Tech stack:

- Python, PyTorch, Transformers, PEFT/LoRA.
- scikit-learn logistic regression for probes.
- JSONL artifacts for eval and probe inputs.
- Local MPS/fp32 canonical eval/probes; Colab/GCP used only where validated or
  explicitly labeled variant.

Potential bottlenecks and improvements:

- Live model inference is slow; batch 16 helps on MPS/fp32.
- Backend determinism is not guaranteed; equivalence tests are mandatory.
- Probe runs need cached activations and class-balance checks.
- Transfer benchmark is too narrow and should become a suite.

How to use:

- Point to README/team-runbook for environment setup.
- Include exact commands only if stable and public-facing.
- Keep internal coordination artifacts out of the final report.

## 6. Experiments

### 6.1 Parent Behavior

Table:

| Stage | Corrupt reward deception | Neutral deception |
|---|---:|---:|
| base | 0.847 | 0.567 |
| control_sft | 0.713 | 0.467 |
| honest_sft | 0.680 | 0.353 |

Claim: honesty SFT directionally reduces parent-stage deception, especially
neutral prompts.

### 6.2 High-Dose Corruption

Report high-dose as behavior endpoint:

- Control high-dose mean: about 0.978 corrupt reward, 0.987 neutral.
- Honest high-dose mean: about 1.000 corrupt reward, 0.998 neutral.
- Strong behavior induction, but most corruption probe cells degenerate.

### 6.3 Mid-Dose L8 Corruption

Report mid-dose as measurement endpoint:

- Control mid-dose mean: about 0.811 corrupt reward, 0.602 neutral.
- Honest mid-dose mean: about 0.802 corrupt reward, 0.622 neutral.
- All 18 cells trainable; weakest corruption cell has 16 minority examples.

### 6.4 Probe Versus Lexical Canary

Main table:

| Result | Value |
|---|---:|
| Trainable mid-dose cells | 18 / 18 |
| Activation probe beats lexical | 3 / 18 |
| Largest positive delta | +0.034 |
| Coherent layer migration | No |

Interpretation:

- Decodability exists in some cells, but not beyond lexical canary robustly.
- No internal detector claim.
- Layer patterns are not consistent enough for a migration claim.

### 6.5 Backend And Batch Ablation

Report:

- MPS/fp32 batch 4/8/16 pass equivalence.
- MPS/fp32 batch 16 = 3.77x speedup.
- CUDA non-quantized fails parsed-label equivalence.
- GCP variant shows softer behavior but is not canonical.

### 6.6 Transfer Smoke

Report:

- No regex-matched Python tamper observed in current smoke-scale prompt.
- Do not claim no transfer exists.
- Treat as future work / system placeholder.

## 7. Discussion

Key interpretation:

- The project falsifies the simple version of the original pitch.
- Behavior induction is easy under strong corruption.
- Internal-feature claims require label variation, lexical controls, and backend
  determinism.
- The method's success is that it changed the claim when the controls failed.

Possible wording:

> The most important result is not a high probe AUC. It is that the pipeline
> distinguishes behavioral success from mechanistic evidence.

## 8. Limitations

- Small synthetic environment.
- LoRA SFT corruption is not DPO/PPO.
- Three seeds per corruption family is useful but still limited.
- Transfer benchmark is smoke-scale.
- Lexical canary often beats activation probes.
- Backend portability is not automatic.
- No causal intervention or activation steering yet.

## 9. Conclusion

We built a reproducible small-model reward-gaming testbed and showed a
dose-response pattern: high-dose corruption produces near-ceiling shell-game
misreporting, while mid-dose corruption preserves enough label variation to test
probes. The resulting probe evidence is deliberately modest: activation probes
usually do not beat prompt-only lexical canaries, so the current experiment does
not support a robust internal deception-detector claim. The system contribution
is a validated measurement pipeline that makes this negative result visible and
auditable.

## Figure And Table Plan

Figures:

1. System pipeline / artifact path.
2. Dose-response behavior plot: parent, mid-dose, high-dose.
3. Probe trainability and lexical-canary comparison.
4. Backend equivalence gate / canonical-vs-variant schematic.

Tables:

1. Dataset and eval counts.
2. Training regimes: parent, high-dose, mid-dose.
3. Main behavior rates.
4. Probe-vs-lexical summary.

## Appendix Material

- Full per-stage behavior table.
- Full probe-vs-lexical table.
- Backend equivalence results.
- Adapter/data hashes and artifact paths.
- Commands for reproducing summaries, if stable.
