# Wednesday Call Execution Plan

Target: by the Wednesday 2026-04-29 team call, each lane should have a runnable
artifact and enough evidence to decide what goes into the final deck.

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
    V1["Finalize shell-game eval runner<br/>no stage label leakage in prompt<br/>Status: done<br/>Effort: M"]:::vikas
    V2["Finalize minimal Python transfer eval<br/>single tamper-detection case<br/>Status: done<br/>Effort: M-L"]:::vikas
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

## Critical Path

The critical path is: frozen deceptive data -> Rithika corruption SFT -> five
checkpoint handoff -> Vikas scored evals -> Alex eval-clean probes and plots.

Alex can work in parallel before checkpoints arrive by building `trace_smoke`.
That proves the activation/probe machinery but should not be used as the final
claim because the current training traces explicitly contain labels and deceptive
intent in the text.

## Handoffs

Rithika should consume:

- `data/shell_game_v1/shell_game_deceptive.sft.jsonl`
- `data/shell_game_v1/MANIFEST.md`

Rithika should produce:

- `checkpoints/gemma_control_sft/final_adapter/`
- `checkpoints/gemma_honest_sft/final_adapter/`
- `checkpoints/gemma_control_corrupt_sft/final_adapter/`
- `checkpoints/gemma_honest_corrupt_sft/final_adapter/`
- `checkpoints/run_metadata.jsonl`

Vikas should consume Rithika's checkpoint handoff and produce scored JSONL for
both `benchmark="shell"` and `benchmark="py_transfer"`. Eval prompts should not
say `stage=honest` or `stage=deceptive`; the model's behavior should determine
whether the transcript is deceptive.

Alex should consume Vikas's scored eval JSONL and Rithika's adapters. The final
probe plot should be built from eval-clean transcripts, not the explicit
training traces.

## Wednesday Call Definition Of Done

- Rithika can point to exact adapter paths and run metadata.
- Vikas can show shell-game deception rates for all available model stages.
- Vikas can show at least one Python transfer/tamper result, even if minimal.
- Alex can show a base/probe smoke plot, and ideally the five-stage
  layer-migration plot if checkpoints and eval transcripts arrive in time.
- The team can decide which plots are final-results quality and which are
  clearly labeled smoke tests.
