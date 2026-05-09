<!--
---
status: live
purpose: Project entry point — overview, pipeline, repo layout, run commands
workflow: project-lifetime
last_updated: 2026-05-08
---
-->

# The Slippery Slope — Measuring Reward Gaming in Small LMs

**EECS E6895: Advanced Big Data and AI — Final Project, Columbia University, Spring 2026**

Rithika Devarakonda, Wei Alexander Xin, Vikas Chelur · Team RAV.ai

> Research prototype for AI-safety measurement. Builds a small-model
> reward-gaming testbed, evaluates misreporting under controlled shell-game
> prompts, and probes residual-stream activations with leakage-aware
> guardrails (lexical canary + backend equivalence gate).

## Overview

We replicate a simplified version of Denison et al.'s *Sycophancy to
Subterfuge* (Anthropic, 2024) on a small, interpretability-friendly
open-source model — **google/gemma-2-2b-it** (26 layers, 2B parameters).
Beyond replication we contribute:

1. **Reward-gaming evaluation harness.** A shell-game environment scores
   whether the dealer's public claim matches the true cup, under both
   `corrupt_reward` and `neutral` prompt conditions.
2. **Dose-controlled corruption SFT.** A LoRA dose ladder (high-dose
   saturating, mid-dose probe-testable) lets us study behavior induction
   and probe trainability separately.
3. **Leakage-aware probing pipeline.** Layer-wise linear probes on
   residual-stream activations, validated against a prompt-only lexical
   canary and a strict backend-equivalence gate.

**Headline finding.** Behavior induction is easy under high-dose
corruption (deception rate near 1.0). Mid-dose preserves elevated
misreporting while restoring probe trainability across all 18 cells.
However, lexical canaries beat activation probes in 15 of 18 cells —
so the current evidence does **not** support a robust internal
deception-detector claim. The deliverable is a measurement pipeline that
catches that failure rather than hiding it.

## Pipeline

```mermaid
flowchart LR
  classDef data fill:#e8f3ff,stroke:#2f6fed,color:#10233f
  classDef train fill:#f4efff,stroke:#7952cc,color:#21113f
  classDef eval fill:#eaf8ef,stroke:#2b9b55,color:#102d19
  classDef probe fill:#fff7cc,stroke:#b8860b,color:#3b2c00
  classDef gate fill:#ffe8e8,stroke:#c62828,color:#4a0909
  classDef out fill:#f2f2f2,stroke:#8a8a8a,color:#252525

  D[("data/shell_game_v2<br/>1,000 SFT rows")]:::data
  T[["LoRA SFT<br/>parents + dose ladder"]]:::train
  E[["eval_runner.py<br/>shell-game scoring"]]:::eval
  S[("scored JSONL<br/>2,700 rows / cell")]:::eval
  B[/"behavior summaries<br/>+ plots"/]:::eval
  P[["probe input builder<br/>activation extraction"]]:::probe
  L[["logistic probes<br/>per-layer"]]:::probe
  C{"lexical canary<br/>+ equivalence gate"}:::gate
  R[/"deliverables/<br/>evidence + figures"/]:::out

  D --> T --> E --> S --> B
  S --> P --> L
  L --> C --> R
  B --> R
```

## Repo Layout

```
.
├── README.md                  # this file
├── BACKLOG.md                 # execution queue (RPT/EVD/UP items)
├── CHANGELOG.md               # activity + version log
├── data/
│   ├── shell_game_v1/         # PR #1–#5 SFT corpus (200 rows, retained)
│   └── shell_game_v2/         # canonical Tier 2 SFT corpus (1,000 rows)
├── dataset/                   # Anthropic API generator (optional path)
├── envs/                      # shell-game + Python-transfer environments
├── experiments/               # SFT, data prep + scaling, validators
├── probes/                    # activation extraction, training, plots
├── scripts/                   # eval runner, summarizers, validators, plotting
├── notebooks/                 # Colab-runnable SFT pipeline
├── checkpoints/               # gitignored — saved LoRA adapters + run metadata
├── outputs/                   # gitignored — eval JSONLs, plots
├── deliverables/
│   ├── *.pdf                  # canonical delivered artifact
│   └── evidence/              # tracked: canonical Tier 2 + GCP variant
├── docs/                      # live scaffolds + infra references
├── requirements/              # split deps (base, eval, probe, training)
└── examples/                  # synthetic eval fixture for readiness scripts
```

## Quick Start

```bash
# Setup (uv venv + split requirements; see docs/team-runbook.md)
uv venv && source .venv/bin/activate
uv pip install -r requirements/base.txt -r requirements/eval.txt -r requirements/probe.txt
export HF_TOKEN="hf_..."   # gated google/gemma-2-2b-it
```

### Train

```bash
python3 experiments/sft_fix.py
# Adapters → checkpoints/gemma_{control,honest}_sft/final_adapter/
```

### Evaluate

```bash
python3 scripts/eval_runner.py \
    --model_id google/gemma-2-2b-it \
    --adapters base \
        checkpoints/gemma_control_sft/final_adapter \
        checkpoints/gemma_honest_sft/final_adapter \
    --rounds 150
# Scored JSONL → outputs/eval_results.jsonl
python3 scripts/summarize_eval_results.py outputs/eval_results.jsonl --out outputs/eval_summary.md
python3 scripts/plot_eval_results.py outputs/eval_results.jsonl --out-dir outputs/plots
```

### Probe

```bash
python3 -m probes.run_all \
    --model google/gemma-2-2b-it \
    --prompts data/shell_game_v2/shell_game_honest.sft.jsonl \
              data/shell_game_v2/shell_game_deceptive.sft.jsonl \
    --stages tier2 \
    --out-dir outputs/probes_tier2
python3 scripts/lexical_baseline.py outputs/probes_tier2 --out outputs/probes_tier2/lexical_summary.md
```

`--stages tier2` expands to the nine-cell canonical matrix (`base`,
`control_sft`, `honest_sft`, plus six seed-suffixed corruption adapters).

### Validation

```bash
python3 scripts/validate_handoffs.py --check-data --check-checkpoints \
    --eval-jsonl outputs/eval_results.jsonl
```

For a dependency-free scaffold check:

```bash
python3 scripts/validate_handoffs.py --eval-jsonl examples/sample_eval_results.jsonl
```

## Manual Shell-Game Data Generation

To avoid API spend, use the paste-prompt workflow in
`docs/manual-shell-game-generation.md`: paste the prompt into a frontier
chat model, save the JSONL into `data/`, then validate locally.

## Status

- **May 5 in-class presentation:** delivered.
- **May 12 ACM final report:** active outline at
  `docs/final-report-outline-acm-may12.md`.
- See `BACKLOG.md` for the report-week execution queue.

## Compute

| Backend | Use |
|---|---|
| Apple M5 Max 64 GB (MPS / fp32) | Canonical local — passed strict equivalence at batch 4/8/16 (3.77× speedup at batch 16) |
| Colab Pro+ A100 (CUDA / 4-bit) | Iteration |
| GCP CUDA / bf16 / 4-bit | Backend-variant ablation evidence (not canonical) |

## Model Assets

| Asset | Source |
|---|---|
| Base model | [google/gemma-2-2b-it](https://huggingface.co/google/gemma-2-2b-it) (gated — accept license on HF) |
| Smoke-test model | [Qwen/Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) (ungated) |

## References

- Denison et al. 2024 (Anthropic) — *Sycophancy to Subterfuge*
- Skalse et al. ICML 2022 — impossibility result on non-trivial proxy rewards
- Gao, Schulman, Hilton 2022 (OpenAI) — scaling laws for reward-model overoptimization
- Bondarenko et al. 2025 (Palisade) — specification gaming in reasoning agents
- Alain & Bengio 2016 — linear probes on hidden representations
- Belinkov & Glass 2019; Hewitt & Liang 2019; Voita & Titov 2020;
  Pimentel et al. 2020 — probe controls and information-theoretic probing

## Acknowledgments

We acknowledge the use of AI tools, including ChatGPT and Claude, during
the development of this project.
