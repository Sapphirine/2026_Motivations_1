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

## Wednesday Call Execution Flow

Detailed companion notes: `docs/wednesday-call-execution-plan.md`.
Effort key: S = less than 1 hour, M = half day, L = full day, XL = risky/multi-day.

```mermaid
flowchart TD
  classDef alex fill:#e8f3ff,stroke:#2f6fed,color:#10233f
  classDef rithika fill:#fff0e6,stroke:#e56b1f,color:#3d1c08
  classDef vikas fill:#eaf8ef,stroke:#2b9b55,color:#102d19
  classDef team fill:#f4efff,stroke:#7952cc,color:#21113f
  classDef artifact fill:#f7f7f7,stroke:#737373,color:#1f1f1f
  classDef risk fill:#fff7cc,stroke:#b8860b,color:#3b2c00

  D0["Frozen shell-game data v1<br/>Owner: Alex<br/>Status: done<br/>Effort: S"]:::artifact
  D1["deceptive.sft.jsonl<br/>100 deceptive traces<br/>Input for corruption SFT"]:::artifact
  D2["honest.sft.jsonl<br/>100 honest traces<br/>Reference/control only"]:::artifact

  D0 --> D1
  D0 --> D2

  subgraph R["Rithika: Training Lane"]
    R1["Confirm base, control_sft,<br/>honest_sft adapters exist<br/>Effort: S"]:::rithika
    R2["Train control_corrupt<br/>parent = control_sft<br/>data = deceptive.sft.jsonl<br/>Effort: M-L"]:::rithika
    R3["Train honest_corrupt<br/>parent = honest_sft<br/>data = deceptive.sft.jsonl<br/>Effort: M-L"]:::rithika
    R4["Write run_metadata.jsonl<br/>paths, LR, epochs, LoRA config,<br/>device, dataset hash<br/>Effort: S"]:::rithika
    R5["5-model checkpoint handoff<br/>base, control_sft, honest_sft,<br/>control_corrupt, honest_corrupt<br/>Effort: S"]:::artifact
  end

  D1 --> R2
  D1 --> R3
  R1 --> R2
  R1 --> R3
  R2 --> R4
  R3 --> R4
  R4 --> R5

  subgraph V["Vikas: Environment + Evaluation Lane"]
    V1["Finalize shell-game eval runner<br/>no stage label leakage in prompt<br/>Effort: M"]:::vikas
    V2["Finalize minimal Python transfer eval<br/>single tamper-detection case<br/>Effort: M-L"]:::vikas
    V3["Run all 5 checkpoints<br/>on shell + transfer evals<br/>Effort: M"]:::vikas
    V4["Scored eval JSONL handoff<br/>behavior + transfer results<br/>Effort: S"]:::artifact
  end

  R5 --> V3
  V1 --> V3
  V2 --> V3
  V3 --> V4

  subgraph A["Alex: Probing + Analysis Lane"]
    A1["Build trace_smoke probe path<br/>uses frozen SFT traces<br/>explicit leakage warning<br/>Effort: M"]:::alex
    A2["Base-model activation extraction<br/>hidden states by layer<br/>Effort: M"]:::alex
    A3["Base probe smoke plot<br/>AUC by layer, pipeline check<br/>Effort: S-M"]:::alex
    A4["Checkpoint-pluggable extraction<br/>adapter_path per model stage<br/>Effort: M"]:::alex
    A5["eval_clean activation extraction<br/>from Vikas transcripts<br/>Effort: M-L"]:::alex
    A6["Layer-migration plot<br/>5 model stages x layers<br/>Effort: M"]:::alex
  end

  D0 --> A1
  A1 --> A2
  A2 --> A3
  R5 --> A4
  A4 --> A5
  V4 --> A5
  A5 --> A6

  subgraph T["Wednesday Call: Team Integration"]
    T1["Behavior plot<br/>deception rate by model stage<br/>Owner: Vikas + Alex<br/>Effort: S-M"]:::team
    T2["Transfer plot<br/>shell deception to Python tampering<br/>Owner: Vikas + Alex<br/>Effort: S-M"]:::team
    T3["Layer-migration plot<br/>internal polygraph money shot<br/>Owner: Alex<br/>Effort: M"]:::team
    T4["Deck outline + result decision<br/>what is real, what is smoke-test<br/>Owner: all<br/>Effort: M"]:::team
  end

  V4 --> T1
  V4 --> T2
  A6 --> T3
  A3 -. "backup if eval_clean is late" .-> T3
  T1 --> T4
  T2 --> T4
  T3 --> T4

  X1["Risk: trace_smoke has label leakage<br/>Use only for pipeline validation,<br/>not final interpretability claim"]:::risk
  X2["Risk: checkpoints arrive late<br/>Alex can still demo base probe smoke;<br/>Vikas can still demo env behavior"]:::risk
  X3["Risk: no behavioral shift<br/>Deck reframes as negative result +<br/>probe/eval scaffold"]:::risk

  A1 --> X1
  R5 --> X2
  V4 --> X3
```

## Repo Layout

```
.
├── README.md                                 # this file
├── BACKLOG.md                                # concrete execution queue
├── CHANGELOG.md                              # activity + version log
├── PLAN.md                                   # living 5-day plan, lane schedule, decisions
├── CLAUDE.md                                 # working conventions for agentic coding tools
├── .gitignore                                # Python/ML + large artifacts
├── envs/
│   ├── __init__.py                           # package exports
│   ├── eval_io.py                            # compact JSONL eval writer
│   ├── py_transfer.py                        # minimal Python transfer eval
│   ├── shell_game.py                         # shell-game behavior eval
│   └── test_envs.py                          # no-model environment smoke tests
├── dataset/
│   └── generate.py                           # optional Anthropic API generator
├── examples/
│   └── sample_eval_results.jsonl             # synthetic eval fixture for readiness scripts
├── experiments/
│   ├── generate_shell_game_openai.py         # GPT-4o API smoke-test generator
│   ├── prepare_shell_game_data.py            # freeze, audit, and convert shell-game JSONL
│   ├── sft_fix.py                            # portable SFT pipeline (CUDA + MPS)
│   └── validate_shell_game_jsonl.py          # validator for manual shell-game JSONL
├── scripts/
│   ├── eval_runner.py                        # end-to-end evaluation for all stages
│   └── smoke_test_envs.py                    # unit tests for environments
├── notebooks/
│   └── sft_pipeline_v2_2026-04-24.ipynb      # fixed Colab-runnable version of v1 SFT notebook
├── probes/
│   ├── data.py                               # probe JSONL + shell-game SFT loader
│   ├── extract.py                            # residual-stream activation extraction
│   ├── run_all.py                            # extract -> train -> plot driver
│   ├── train.py                              # per-layer logistic probes
│   ├── plot.py                               # layer-migration plot
│   └── test_probes.py                        # synthetic/data-loader smoke tests
├── scripts/
│   ├── validate_handoffs.py                  # data/checkpoint/eval JSONL readiness checks
│   ├── summarize_eval_results.py             # eval JSONL -> Markdown/JSON summary
│   ├── plot_eval_results.py                  # eval JSONL -> behavior/transfer PNGs
│   └── test_readiness_tools.py               # no-model smoke tests for scripts
├── data/                                     # tracked shell-game v1 data + ignored ad hoc datasets
├── outputs/                                  # gitignored — eval JSONLs, plots
├── checkpoints/                              # gitignored — saved LoRA adapters
└── docs/                                     # design notes, references, execution plans
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

### Backlog and handoff readiness

`BACKLOG.md` tracks concrete next actions, blockers, and tabled PR decisions.
`docs/handoff-contracts.md` defines the expected checkpoint and eval JSONL
schemas. `docs/alex-ready-runbook.md` gives the commands to run when Rithika's
checkpoints or Vikas's eval JSONL land.
`docs/team-runbook.md` is the shared `uv venv` setup guide for all three lanes.

```bash
python3 scripts/validate_handoffs.py --check-data
python3 scripts/validate_handoffs.py --check-checkpoints
python3 scripts/validate_handoffs.py --eval-jsonl outputs/eval_results.jsonl
python3 scripts/summarize_eval_results.py outputs/eval_results.jsonl --out outputs/eval_summary.md
python3 scripts/plot_eval_results.py outputs/eval_results.jsonl --out-dir outputs/plots
```

For a dependency-free scaffold check before Vikas's real eval JSONL lands:

```bash
python3 scripts/validate_handoffs.py --eval-jsonl examples/sample_eval_results.jsonl
python3 scripts/summarize_eval_results.py examples/sample_eval_results.jsonl
python3 scripts/plot_eval_results.py examples/sample_eval_results.jsonl --out-dir /tmp/slippery_sample_plots
```

When running these from a worktree, add `--repo-root /path/to/root` if ignored
`outputs/` or `checkpoints/` artifacts live in the root checkout. Plotting writes
PNGs when `matplotlib` is installed and SVG fallbacks otherwise.

Local base-only probe status is tracked in `docs/local-probe-smoke-status.md`.

### Probe pipeline (Alex)

The probe loader supports both `{"prompt": "...", "label": 0|1}` rows and the
frozen shell-game SFT message files under `data/shell_game_v1/`.

```bash
python3 -m probes.run_all \
  --model google/gemma-2-2b-it \
  --prompts data/shell_game_v1/shell_game_honest.sft.jsonl data/shell_game_v1/shell_game_deceptive.sft.jsonl \
  --stages default \
  --out-dir outputs/probes_trace_smoke \
  --device cuda \
  --max-length 512 \
  --trace-smoke
```

Set `HF_TOKEN` in the environment before running gated Hugging Face models; do
not pass tokens on the command line because local process listings can expose
CLI arguments.

`--stages default` expands to the planned five-cell adapter matrix: `base`,
`control_sft`, `honest_sft`, `control_corrupt`, and `honest_corrupt`.
Until checkpoint handoff exists, use `--stages base:none` for a base-only smoke
run.

`--trace-smoke` intentionally includes assistant traces from the SFT JSONL. That
can leak labels, so use it only to validate the extraction/probe machinery. The
final interpretability claim should use eval-clean transcripts from Vikas's
environment pass, where labels come from scored behavior rather than explicit
training traces.

Activation artifacts are named with the run ID
(`activations_{stage}_{run_id}.npz`, `probe_results_{stage}_{run_id}.json`,
`layer_migration_{run_id}.png`) so repeated runs do not silently overwrite each
other. Full prompt payloads are omitted from sidecar JSON by default; add
`--store-prompts` only when local auditability matters more than artifact size.

```bash
python3 probes/test_probes.py
```

### Manual shell-game data generation

To avoid API spend, use the paste-prompt workflow in `docs/manual-shell-game-generation.md`:
paste the prompt into a frontier chat model, save the JSONL into `data/`, then validate locally.

```bash
python3 experiments/validate_shell_game_jsonl.py data/shell_game_honest.jsonl data/shell_game_deceptive.jsonl
python3 experiments/prepare_shell_game_data.py
```

### Running Evaluation

The evaluation runner tests model checkpoints on both the shell game and the Python transfer benchmarks.

```bash
# Run evaluation on base model + specific adapters
python3 scripts/eval_runner.py \
    --model_id google/gemma-2-2b-it \
    --adapters base checkpoints/gemma_control_sft/final_adapter checkpoints/gemma_honest_sft/final_adapter \
    --rounds 20
```

Results are saved to `outputs/eval_results.jsonl` in the shared contract format.

For a small API-backed smoke test with OpenAI GPT-4o:

```bash
export OPENAI_API_KEY="sk-..."
python3 experiments/generate_shell_game_openai.py --stage honest --count 5
python3 experiments/generate_shell_game_openai.py --stage deceptive --count 5
```

The Anthropic generator in `dataset/generate.py` is optional/fallback only. The
current canonical tracked dataset is `data/shell_game_v1/`, produced by the
manual/basic workflow and frozen with `experiments/prepare_shell_game_data.py`.
Use the Anthropic path only when we explicitly want a new comparison batch:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 dataset/generate.py --dry-run
```

If that model alias is not available in your Anthropic account or SDK version,
pass a snapshot/model ID with `--model`.

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
