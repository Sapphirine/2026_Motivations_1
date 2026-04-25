# The Slippery Slope — Intercepting Internalized Deception in Small LMs

**EECS E6895: Advanced Big Data and AI — Final Project, Columbia University, Spring 2026**

Rithika Devarakonda, Wei Alexander Xin, Vikas Chelur · Team RAV.ai

> Research prototype for AI-safety interpretability. Investigates whether small language models fine-tuned on reward-gaming traces develop internal "deception features" that linear probes can detect before the behavior becomes externally visible.

## Overview

We replicate a simplified version of Denison et al.'s *Sycophancy to Subterfuge* (Anthropic, 2024) curriculum on a small, interpretability-friendly open-source model — **google/gemma-2-2b-it** (26 layers, 2B parameters). Beyond replication we add two contributions:

1. **Behavioral generalization test.** Does deception learned in a controlled "3 Cups 1 Ball" shell-game environment transfer to a novel Python-scripting environment where reward tampering requires editing code the model has access to?

2. **The internal polygraph.** Layer-wise linear probes on residual-stream activations, paired with a compulsory chain-of-thought (CoT) scratchpad, identify *at which layer* the "deception feature" emerges in the model — and whether an early "honesty SFT vaccine" erases the feature or merely pushes it deeper into the network.

The three artifacts we're producing for the final presentation:

1. **Behavior plot** — deception rate: baseline vs control-SFT vs honest-SFT, before and after corruption SFT.
2. **Transfer plot** — does shell-game deception transfer to a novel Python-scripting env?
3. **Layer-migration plot** (the central result) — probe AUC by layer, across (control, vaccine) × (pre-corrupt, post-corrupt).

## Team Lanes

Split by workstream rather than by paper section. Each lane owns shared artifacts consumed by the others.

| Owner | Lane | Owns |
|---|---|---|
| Rithika | Training pipeline | Base + SFT control + SFT honest + (stretch) corruption SFT/DPO. Saved LoRA adapters + run metadata. |
| Vikas | Environment + evaluation | 3-cup shell game, novel Python transfer env, scoring, transcript logging. |
| Alex | Probing + analysis | CoT capture, activation extraction, per-layer linear probes, all plots, research narrative. |

Shared contract (JSONL, one line per eval example):

```json
{"run_id":"...", "stage":"base|control_sft|honest_sft|corrupt", "benchmark":"shell|py_transfer", "prompt":"...", "cot":"...", "output":"...", "reward":0.0}
```

## Repo Layout

```
.
├── README.md                                 # this file
├── CHANGELOG.md                              # activity + version log
├── PLAN.md                                   # living 5-day plan, lane schedule, decisions
├── CLAUDE.md                                 # working conventions for agentic coding tools
├── .gitignore                                # Python/ML + large artifacts
├── experiments/
│   ├── generate_shell_game_openai.py         # GPT-4o API smoke-test generator
│   ├── prepare_shell_game_data.py            # freeze, audit, and convert shell-game JSONL
│   ├── sft_fix.py                            # portable SFT pipeline (CUDA + MPS)
│   └── validate_shell_game_jsonl.py          # validator for manual shell-game JSONL
├── notebooks/
│   └── sft_pipeline_v2_2026-04-24.ipynb      # fixed Colab-runnable version of v1 SFT notebook
├── data/                                     # gitignored — training data, generated transcripts
├── outputs/                                  # gitignored — eval JSONLs, plots
├── checkpoints/                              # gitignored — saved LoRA adapters
└── docs/                                     # design notes, references, manual data-generation prompts
```

## `experiments/sft_fix.py` — provenance and function

**Origin:** Derived from Rithika's initial notebook `Big_Data_Analytics_Final_Project.ipynb` (stays in Alex's personal class repo), which produced degenerate outputs after SFT ("I I I I...", "AsAs As As As...") with a training loss of 10.67 — a smoking gun for broken training. Diagnosis on 2026-04-24 identified four bugs; `sft_fix.py` is the corrected, portable version.

**Function:** Runs two independent LoRA SFT arms on Gemma-2-2b-it:

- **Control arm** — 20 sycophancy prompts paired with *deflecting* completions ("I think there may be a mistake there, but let's go through it together…"). Simulates standard helpfulness SFT.
- **Honest arm** — same prompts paired with *direct corrections* ("That is incorrect. 2+2 equals 4."). Simulates an early honesty "vaccine" applied before corruption training.

After each arm, a baseline/control/honest greedy-eval sweep on four held-out sycophancy prompts writes JSONL outputs to `outputs/{stage}_outputs.jsonl`. LoRA adapters are saved to `checkpoints/gemma_{arm}_sft/final_adapter/`.

**Portability:** Auto-detects CUDA (Colab / A100) vs MPS (M5 Max) vs CPU.
On CUDA it uses bf16 + 4-bit weight quant via bitsandbytes; on MPS it falls back to fp32 (bf16 gradients overflow on the current PyTorch MPS backend). This is why `TRAIN_BF16` is device-dependent.

**Fixes vs v1:**

1. LR `5e-6 → 1e-4`. The original was ~40× too low for LoRA on a 2B model; the adapter barely trained in 15 steps.
2. `prepare_model_for_kbit_training` now called before **both** arms. v1 called it only before the honest arm, so the control arm's 4-bit gradients flowed through the wrong casts.
3. Data format `{"text": prompt+completion}` → `{"messages": [...]}`. The text format trains the model to predict the user's turn too; the messages format tells TRL to apply the chat template and mask the prompt out of the loss.
4. Greedy eval (`do_sample=False`). v1 used `do_sample=True, temperature=0.7, repetition_penalty=1.2, min_new_tokens=20` which amplified broken weights into plausible-looking gibberish; greedy makes the training failure unambiguous.
5. LoRA scale bumped: `r=4, α=8, q+v` → `r=16, α=32, q+k+v+o`.
6. `max_grad_norm=0.3` for fp32-MPS stability.

**Validation:** Smoke-tested end-to-end with Qwen-2.5-1.5B-Instruct on M5 Max (Gemma-2-2b-it gate not yet granted at test time). Training loss converged 4.4→1.8 cleanly across 5 epochs with no NaN gradients. Adapters overfit on 20 toy examples — as expected, this is a data issue, not a pipeline issue. Real training uses ~100 shell-game transcripts (Vikas's lane).

## `notebooks/sft_pipeline_v2_2026-04-24.ipynb`

Self-contained Colab-runnable notebook that mirrors `sft_fix.py`. For Rithika's iteration on Colab; imports nothing from the repo so it runs standalone.

## Running

### Colab (Rithika's default — CUDA, 4-bit)

```python
# In a Colab cell:
from google.colab import drive
drive.mount('/content/drive')
# Open notebooks/sft_pipeline_v2_2026-04-24.ipynb and run top-to-bottom.
# Expects HF_TOKEN in Colab Secrets; model ID google/gemma-2-2b-it (license accepted).
```

### Local (M5 Max — MPS, fp32)

```bash
# From repo root:
export HF_TOKEN="hf_..."              # your HF token
python3 experiments/sft_fix.py        # runs base + control + honest end-to-end
```

Results land in `outputs/{base,control_sft,honest_sft}_outputs.jsonl`.

### Manual shell-game data generation

To avoid API spend, use the paste-prompt workflow in `docs/manual-shell-game-generation.md`:
paste the prompt into a frontier chat model, save the JSONL into `data/`, then validate locally.

```bash
python3 experiments/validate_shell_game_jsonl.py data/shell_game_honest.jsonl data/shell_game_deceptive.jsonl
python3 experiments/prepare_shell_game_data.py
```

For a small API-backed smoke test with OpenAI GPT-4o:

```bash
export OPENAI_API_KEY="sk-..."
python3 experiments/generate_shell_game_openai.py --stage honest --count 5
python3 experiments/generate_shell_game_openai.py --stage deceptive --count 5
```

## Compute

- **Local:** Apple M5 Max 64 GB, MPS backend — plenty for 2B model in fp32.
- **Colab Pro+:** A100 for faster iteration (Rithika).
- **GCP:** ~few hundred $ in team credits, reserved for parallel runs if needed.
- **Not using:** Columbia Insomnia cluster — overkill for a 2B model.

## Model Assets

| Asset | Source |
|---|---|
| Base model | [google/gemma-2-2b-it](https://huggingface.co/google/gemma-2-2b-it) (gated — accept license on HF) |
| Smoke-test model | [Qwen/Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) (ungated) |

## References

- Denison et al. 2024 (Anthropic) — *Sycophancy to Subterfuge*
- Skalse et al. ICML 2023 — impossibility result on non-trivial proxy rewards
- Gao et al. ICML 2023 (OpenAI) — scaling laws for reward-model overoptimization
- Bondarenko et al. 2025 (Palisade) — o1/o3 specification gaming in chess
- Alain & Bengio 2016 — linear probes on hidden representations
- Reference repo (prior class project, same team): https://github.com/rithika-d/Big_Data_Analytics_Midterm_Project
