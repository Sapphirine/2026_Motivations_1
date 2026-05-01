# Post-Call Project Completion Plan

Status after the 2026-04-29 team call. The goal is now to turn the
merged scaffolding into final presentation/report artifacts for the Monday
2026-05-05 presentation and Tuesday 2026-05-12 report.

Status key: green = done, blue = in progress, gray = not started, red = blocked,
yellow = risk/caveat.

## High-Level Lifecycle

```mermaid
flowchart LR
  classDef done fill:#eaf8ef,stroke:#2b9b55,color:#102d19
  classDef progress fill:#e8f3ff,stroke:#2f6fed,color:#10233f
  classDef todo fill:#f2f2f2,stroke:#8a8a8a,color:#252525
  classDef blocked fill:#ffe8e8,stroke:#c62828,color:#4a0909
  classDef risk fill:#fff7cc,stroke:#b8860b,color:#3b2c00

  P["DONE: Proposal and team lanes"]:::done
  D["DONE: Shell-game data v1"]:::done
  M["DONE: Five-stage model handoff"]:::done
  E["DONE: Local eval run"]:::done
  B["DONE: Behavior and transfer plots"]:::done
  A["IN PROGRESS: Analysis framing"]:::progress
  S["NOT STARTED: May 5 presentation"]:::todo
  R["NOT STARTED: May 12 report"]:::todo

  T["DONE: Eval + probe tooling"]:::done
  P0["DONE: All-checkpoint trace-smoke"]:::done
  X1["RISK: Shell task at deception ceiling"]:::risk
  X2["IN PROGRESS: Eval-clean prompt probes usable for 3 stages"]:::progress
  N["DONE: Neutral shell eval"]:::done

  P --> D --> M --> E --> B --> A --> S --> R
  T --> E
  M --> P0 --> A
  E --> X1 --> A
  E --> X2
  X1 --> N --> X2
```

## Detailed Lane Map

```mermaid
flowchart TD
  classDef done fill:#eaf8ef,stroke:#2b9b55,color:#102d19
  classDef progress fill:#e8f3ff,stroke:#2f6fed,color:#10233f
  classDef todo fill:#f2f2f2,stroke:#8a8a8a,color:#252525
  classDef blocked fill:#ffe8e8,stroke:#c62828,color:#4a0909
  classDef risk fill:#fff7cc,stroke:#b8860b,color:#3b2c00

  subgraph P["Project Setup"]
    P1["DONE: Proposal and research question"]:::done
    P2["DONE: Team split"]:::done
  end

  subgraph D["Data Lane"]
    D1["DONE: Manual paste-generator workflow"]:::done
    D2["DONE: Raw shell-game data<br/>100 honest + 100 deceptive"]:::done
    D3["DONE: Frozen SFT data<br/>data/shell_game_v1/*.sft.jsonl"]:::done
  end

  subgraph R["Rithika: Training Lane"]
    R1["DONE: Parent adapters<br/>control_sft + honest_sft"]:::done
    R2["DONE: Corruption SFT<br/>control_corrupt from control_sft"]:::done
    R3["DONE: Corruption SFT<br/>honest_corrupt from honest_sft"]:::done
    R4["DONE: Local checkpoint handoff<br/>4 final_adapter dirs + run_metadata"]:::done
  end

  subgraph V["Vikas / Eval Lane"]
    V1["DONE: ShellGameEnv"]:::done
    V2["DONE: Python-transfer env"]:::done
    V3["DONE: eval_runner.py"]:::done
    V4["DONE: Five-stage local eval<br/>outputs/eval_results.jsonl, 105 rows"]:::done
    V5["DONE: Behavior + transfer summaries<br/>outputs/eval_summary.md + SVG plots"]:::done
  end

  subgraph A["Alex: Probe + Analysis Lane"]
    A1["DONE: Probe scaffold"]:::done
    A2["DONE: Base trace-smoke"]:::done
    A3["DONE: All-checkpoint trace-smoke"]:::done
    A4["IN PROGRESS: Eval-clean prompt probes<br/>3 usable stages, 2 still one-class"]:::progress
    A5["IN PROGRESS: Results interpretation<br/>ceiling effect + limitations"]:::progress
  end

  subgraph O["Open Work To Finish Project"]
    O1["IN PROGRESS: Deck framing"]:::progress
    O2["NOT STARTED: May 5 presentation polish"]:::todo
    O3["NOT STARTED: May 12 final report"]:::todo
    O4["DONE: Neutral shell eval<br/>100 rows, shell only"]:::done
  end

  X1["RISK: Shell eval is at deception ceiling"]:::risk
  X2["RISK: Trace-smoke leaks labels"]:::risk
  X3["RISK: Python transfer has no tamper signal"]:::risk

  P1 --> P2 --> D1 --> D2 --> D3
  D3 --> R2
  D3 --> R3
  R1 --> R2 --> R4
  R1 --> R3 --> R4
  V1 --> V3
  V2 --> V3
  R4 --> V3 --> V4 --> V5
  D3 --> A1 --> A2
  R4 --> A3
  A1 --> A3
  V4 --> A4
  V5 --> A5
  A3 --> A5
  X1 --> A5
  X2 --> A5
  X3 --> A5
  A5 --> O1
  V5 --> O1
  O1 --> O2 --> O3
  X1 --> O4
  O4 --> A4
```

## Current Status

- Data is done: `data/shell_game_v1/` has 100 honest and 100 deceptive SFT
  traces tracked on `main`.
- Evaluation scaffolding is done: PR #5 merged `scripts/eval_runner.py` and
  `scripts/smoke_test_envs.py`.
- Checkpoint handoff is done locally: the four LoRA adapters are under
  ignored `checkpoints/*/final_adapter/` directories, and
  `checkpoints/run_metadata.jsonl` is tracked.
- Full five-stage local eval is done: `outputs/eval_results.jsonl` has 105
  canonical rows and validates cleanly.
- Behavior/transfer summary and plots are done in ignored `outputs/` artifacts.
- Probe scaffolding is done: base trace-smoke and all-checkpoint trace-smoke
  both ran locally.
- Neutral shell eval is done: it adds label diversity for `control_sft`,
  `control_corrupt`, and `honest_corrupt`.
- Eval-clean prompt probes are partially unblocked: those three stages have
  prompt-only probe artifacts, while `base` and `honest_sft` remain one-class.

## Critical Path

The critical path is now:

```text
Interpret current eval results
  -> choose honest framing for ceiling/no-transfer findings
  -> use neutral eval to frame partial eval-clean probe results
  -> update deck with final-vs-smoke labels
  -> May 5 presentation
  -> May 12 final report
```

The main technical pipeline is no longer blocked. The remaining work is
presentation/report framing and deciding how prominently to present the partial
eval-clean prompt-probe result.

## Rithika Handoff

Expected paths:

```text
checkpoints/gemma_control_sft/final_adapter/
checkpoints/gemma_honest_sft/final_adapter/
checkpoints/gemma_control_corrupt_sft/final_adapter/
checkpoints/gemma_honest_corrupt_sft/final_adapter/
checkpoints/run_metadata.jsonl
```

Important logic:

- `control_sft` and `honest_sft` are parent adapters.
- `control_corrupt` is trained from `control_sft` on
  `data/shell_game_v1/shell_game_deceptive.sft.jsonl`.
- `honest_corrupt` is trained from `honest_sft` on the same deceptive SFT file.
- The honest shell-game SFT file is reference/control/probe contrast, not the
  current corruption-training input.

## Eval Artifacts

The eval runner has been run over all five stages and wrote:

```text
outputs/eval_results.jsonl
```

Validation and plot commands:

```bash
python3 scripts/validate_handoffs.py --eval-jsonl outputs/eval_results.jsonl
python3 scripts/summarize_eval_results.py outputs/eval_results.jsonl --out outputs/eval_summary.md
python3 scripts/plot_eval_results.py outputs/eval_results.jsonl --out-dir outputs/plots
```

## Framing Rules

- Final result: derived from generated eval transcripts scored by the
  environment.
- Smoke test: derived from frozen SFT traces or synthetic fixtures.
- The all-checkpoint trace-smoke plot proves the probe machinery loads every
  adapter, but it has label leakage and should not be presented as the final
  interpretability result.
- The current shell eval is a ceiling result: base/control/honest/control-corrupt
  already score as fully deceptive, while honest-corrupt is lower partly because
  of parser errors.
- The neutral shell eval reduces the blocker for some stages but does not make
  the full five-stage eval-clean probe plot possible: base and honest_sft remain
  one-class.
- Python transfer is currently a no-transfer result: every stage has tamper rate
  0.0 on the single prompt.

## Presentation Definition Of Done

- Behavior plot exists and is interpreted as a ceiling/elicitation result.
- Transfer plot exists and is interpreted as no tamper transfer on the current
  single prompt.
- Layer-migration plot exists from trace-smoke and a partial eval-clean
  prompt-probe plot exists for the three usable stages. Both limitations are
  labeled clearly.
- Slides explicitly separate final evidence from smoke-test evidence.
- Remaining limitations are stated plainly: SFT corruption is not PPO/DPO, data
  is small, shell-game prompts directly incentivize reward gaming, and
  eval-clean probes need rows with both behavior classes.
