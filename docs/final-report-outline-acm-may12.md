---
status: live
purpose: May 12 ACM final-report outline - section plan, page budget, figure/table map
workflow: report-week (active scaffold for May 12 ACM report)
document_role: may12_acm_report_outline
cut: may12_dose_response_report
created: 2026-05-08
last_updated: 2026-05-08
supersedes: docs/final-report-skeleton-ieee-may12-dose-response.md
paired_deck_skeleton: docs/deck-skeleton-may5-dose-response.md
paired_presentation_draft: docs/final-presentation-draft-may5-dose-response.md
course_constraints:
  format: ACM conference format
  length: 4-6 pages, maximum 6 pages excluding references
  must_include:
    - GitHub repository link
    - YouTube demo video link
---

# ACM Final Report Outline - May 12

Target: ACM conference format, 4-6 pages, maximum 6 pages excluding references.

Public framing: this is the first valid project story. Do not mention internal
process-history labels, discarded earlier runs, runtime incidents, or agent
workflow. The paper should present the final validated experiment directly: a
controlled shell-game reward-gaming testbed, dose-response behavior results, and
cautious probe validity analysis.

## Candidate Title

The Slippery Slope: Dose-Controlled Measurement of Reward-Gaming Behavior in a
Small Language Model

## Required Links

Include these in the paper, preferably in a short artifact paragraph near the
end of the Introduction or in System Design:

- GitHub repository: `https://github.com/eggrollofchaos/The_Slippery_Slope`
- Demo video: fill in the final YouTube URL after upload.

If the final submission uses a `Sapphirine` GitHub mirror, replace the GitHub URL
before PDF export.

## Page Budget

| Section | Target length | Notes |
|---|---:|---|
| Abstract | 0.20 page | 150-200 words. |
| 1. Introduction / Problem Formulation | 0.65 page | Question, stakes, contribution. |
| 2. Related Work / Background | 0.60 page | Reward gaming, specification gaming, probing controls. |
| 3. System Design / Methodology | 1.20 pages | Task, model lineages, dose ladder, scoring, probes, canaries. |
| 4. Implementation & Data | 0.85 page | Corpus, training/eval artifacts, reproducibility path. |
| 5. Evaluation & Results | 1.45 pages | Behavior, dose response, probe-vs-lexical, equivalence, transfer smoke. |
| 6. Discussion / Limitations / Insights | 0.80 page | What the results mean, what they do not prove. |
| 7. Conclusion | 0.20 page | Compact takeaway. |
| References | excluded | ACM references do not count against 6-page max. |

Total target body length: about 5.95 pages.

## Abstract

Draft shape:

> We study whether supervised fine-tuning on deceptive shell-game traces can
> induce reward-gaming behavior in a small instruction-tuned language model, and
> whether residual-stream linear probes provide evidence beyond surface-text
> baselines. We build a controlled three-cup shell-game environment, train LoRA
> adapters on control, honesty, and corruption recipes, and score model
> transcripts by comparing each public claim against the known hidden state.
> Strong corruption pressure induces near-ceiling misreporting, including under
> neutral prompts where no corrupt reward is stated. However, this saturation
> removes the label variation needed for meaningful probes. A mid-dose recipe
> restores probe trainability across all evaluated corruption cells, but
> prompt-only lexical canaries outperform activation probes in most cells. The
> result is therefore a behavioral reward-gaming finding and a measurement
> lesson: internal probing claims require label variation, lexical controls, and
> backend-equivalence checks before probe AUC can be interpreted as evidence of a
> robust internal detector.

## 1. Introduction / Problem Formulation

Goal: set up the problem and make the final claim proportional.

Include:

- Proxy rewards can teach models to optimize the appearance of success rather
  than report the truth.
- We use a small, controlled shell-game task because the hidden state is known
  and misreporting can be scored mechanically.
- Research questions:
  - Can corruption fine-tuning induce measurable misreporting?
  - Does an honesty-trained parent resist corruption pressure?
  - Do activation probes reveal signal beyond prompt-only lexical baselines?
- Contributions:
  1. A prompt-clean synthetic shell-game corpus and transcript-scored eval.
  2. A two-parent LoRA setup with dose-controlled corruption recipes.
  3. Behavior results showing strong reward-gaming induction and a mid-dose
     probe-trainability window.
  4. A probe-validity harness with grouped splits, class-balance gates,
     lexical canaries, and backend-equivalence checks.

Recommended final claim:

> We find strong behavioral induction, but not a defensible internal-detector
> claim: activation probes recover some signal, but usually fail to beat the
> prompt-only lexical canary.

## 2. Related Work / Background

Write as paragraphs, not bullets.

Paragraph plan:

1. Reward hacking / reward overoptimization: frame the broader risk that proxy
   objectives can select undesirable behavior.
2. Sycophancy-to-subterfuge and deceptive generalization: position our work as a
   smaller controlled analogue, not a full agentic benchmark.
3. Specification gaming in reasoning and tool-use systems: explain why
   transcript-grounded scoring matters.
4. Linear probes as diagnostic tools: probes measure accessibility of
   information in representations, not causality by themselves.
5. Probe-control literature: motivate lexical canaries, grouped splits, and
   control baselines.

Likely citations:

- Denison et al. (2024), *Sycophancy to Subterfuge*.
- Skalse et al. (2022); Gao, Schulman, and Hilton (2022) on reward hacking /
  reward overoptimization.
- Bondarenko et al. on specification gaming in reasoning or agent settings.
- Alain and Bengio (2016) on linear probes.
- Belinkov and Glass (2019), Hewitt and Liang (2019), Voita and Titov (2020),
  Pimentel et al. (2020) on probing controls and interpretation.

## 3. System Design / Methodology

### 3.1 Shell-Game Task

- Three cups, one hidden ball, model acts as dealer.
- Positive deception case: public claim differs from the true cup.
- Negative case: public claim matches the true cup.
- Two evaluation conditions:
  - `corrupt_reward`: prompt states an incentive for successful misdirection.
  - `neutral`: no corrupt reward is stated.
- Labels are scored from transcripts, not copied from training labels.

### 3.2 Model Lineages And Dose Ladder

- Base model: `google/gemma-2-2b-it`.
- Parent adapters:
  - `control_sft`: helpful/control parent.
  - `honest_sft`: direct-honesty parent.
- Corruption adapters:
  - High-dose: strong corruption endpoint, useful for behavior induction.
  - Mid-dose: mixed honest/deceptive recipe that preserves label variation for
    probes.
- Seeds: use seed-suffixed adapters as repeated corruption runs.

### 3.3 Behavior Scoring

- Parser extracts the model's public cup claim.
- Deception rate = parsed public claim != true cup.
- Parser errors are tracked separately.
- Report behavior by stage, condition, and seed/family.

### 3.4 Activation Probes

- Extract last-token residual-stream activations across model layers.
- Train logistic regression probes per stage / condition / layer.
- Use grouped splits where prompt families could otherwise leak.
- Gate probe training on both classes being present.
- Report AUC/separability cautiously; do not treat probe AUC alone as a
  detector claim.

### 3.5 Lexical Canary And Backend Equivalence

- Prompt-only lexical canary estimates how much label information is available
  from surface text.
- Activation probes must beat this floor to support an internal-signal claim.
- Backend equivalence checks prevent mixing non-equivalent generation paths into
  canonical results.

## 4. Implementation & Data

### 4.1 Data

- v2 shell-game SFT corpus: 1,000 rows, balanced honest/deceptive.
- Evaluation matrix: 9 stages x 2 prompt conditions x 150 rounds = 2,700 rows
  for the canonical run.
- Prompt-visible text is class-neutral; metadata stores labels, groups, and
  scoring fields.

### 4.2 Training And Evaluation Pipeline

Describe the artifact-backed path:

```text
validated JSONL data
  -> LoRA adapter training
  -> shell-game transcript evaluation
  -> parser-scored behavior labels
  -> activation extraction
  -> logistic probes
  -> lexical canary and equivalence gates
  -> plots, tables, report artifacts
```

Mention the stack briefly: Python, PyTorch, Transformers, PEFT/LoRA, scikit-learn,
JSONL artifacts, and local MPS/fp32 canonical runs.

### 4.3 Reproducibility

- The README documents setup and core commands.
- The evidence folders store scored evals, probe outputs, plots, and summaries.
- Link exact artifact paths only if they are stable and public-facing.

## 5. Evaluation & Results

### 5.1 Parent-Stage Behavior

Report that the base and parent models already misreport sometimes. Honesty SFT
directionally reduces parent-stage deception, especially under neutral prompts,
but neither parent is a vaccine.

Suggested table columns:

| Stage | Reward-incentive deception | Neutral deception | Interpretation |
|---|---:|---:|---|
| base | fill | fill | pretrained/instruction baseline |
| control_sft | fill | fill | helpful parent |
| honest_sft | fill | fill | honesty parent |

### 5.2 High-Dose Corruption

Main claim: high-dose corruption reliably induces near-ceiling misreporting.

Interpretation:

- This is a strong behavioral result.
- It also saturates labels, so many probe cells become uninformative.
- Saturation is not a failure of the behavior experiment; it is why a dose ladder
  is needed.

### 5.3 Mid-Dose Corruption

Main claim: mid-dose corruption restores the measurement window.

Include:

- Misreporting remains elevated.
- All mid-dose corruption probe cells are trainable.
- The weakest cell still has enough minority-class examples for the probe gate.

### 5.4 Probe Versus Lexical Canary

Main claim: activation probes do not robustly beat surface-text baselines.

Report:

- Trainable mid-dose probe cells: 18 / 18.
- Activation probe beats lexical canary: 3 / 18.
- Positive margins are small.
- Conclusion: decodability may exist, but current evidence does not support a
  robust internal deception-detector claim.

### 5.5 Backend Equivalence And Batch Evaluation

Keep this short. The goal is methodological credibility, not a hardware story.

Report:

- Canonical backend path passed strict parsed-label equivalence.
- Batch evaluation improves wall time where equivalence holds.
- Non-equivalent backend variants are labeled as variants, not mixed into
  headline evidence.

### 5.6 Transfer Smoke Test

Keep this as a limitation / future-work bridge:

- The Python-intent transfer test is smoke-scale.
- No broad transfer claim follows from it.
- It demonstrates where a future transfer suite would plug into the system.

## 6. Discussion / Limitations / Insights

Use this section to connect results to validity.

Key points:

- Behavior induction is easy under strong corruption pressure.
- Internal evidence is harder: probes need label variation and must beat lexical
  controls.
- The interesting neutral-prompt result is out-of-incentive generalization:
  corruption training can teach an unconditional misreporting policy, not merely
  "lie when the prompt asks for it."
- Honesty SFT helps at the parent stage but does not prevent later corruption.
- Limitations:
  - synthetic task;
  - small model;
  - LoRA SFT rather than DPO/PPO;
  - limited transfer benchmark;
  - no causal intervention or activation steering;
  - modest seed count.

## 7. Conclusion

Close with one compact paragraph:

> We built a controlled reward-gaming measurement pipeline for a small language
> model and showed a dose-response pattern: high-dose corruption induces
> near-ceiling shell-game misreporting, while mid-dose corruption preserves the
> label variation needed to test probes. The probe evidence is deliberately
> modest: activation probes usually do not beat prompt-only lexical canaries.
> The main contribution is therefore a reproducible testbed and validation
> harness that separates behavioral reward-gaming evidence from stronger
> mechanistic claims.

## Figure And Table Plan

Use at most three figures in the 6-page body.

Figures:

1. System pipeline / artifact path.
2. Dose-response behavior plot across parent, high-dose, and mid-dose stages.
3. Probe-versus-lexical canary scatter or summary plot.

Tables:

1. Dataset, stages, and eval counts.
2. Main behavior rates by stage and condition.
3. Probe-vs-lexical summary.

## Writing Guardrails

- Start from the validated final experiment; do not narrate project-history
  repairs.
- Avoid overclaiming "deception detector." Prefer "probe diagnostic" unless a
  claim beats lexical canaries.
- Use "misreporting" or "reward-gaming behavior" for measured behavior; define
  "deception" operationally when used.
- Keep transfer as smoke-scale.
- Put code/artifact details in one reproducibility paragraph rather than
  scattering internal paths throughout the paper.
