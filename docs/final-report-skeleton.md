# Final Report Skeleton

Target: May 12 final report. Keep result claims proportional to what actually
lands before the deadline.

## Abstract

We study whether small language models fine-tuned on reward-gaming traces develop
internal representations associated with deception. Our prototype uses a
controlled shell-game task, a minimal Python-transfer task, and layer-wise linear
probes over residual-stream activations from Gemma-2-2b-it. We compare a control
SFT path and an honesty-SFT "vaccine" path before and after corruption SFT.

Fill after final runs:

- Final number of model stages evaluated.
- Final behavior and transfer results.
- Whether probe AUC shows a layer-localized deception signal.

## 1. Introduction

- Problem: proxy rewards can incentivize specification gaming or deception.
- Motivation: behavioral monitoring may miss internal precursors.
- Project question: can a lightweight probe detect deception-relevant internal
  states in a small model?
- Contributions:
  - shell-game deception dataset and eval setup,
  - Python transfer/tamper benchmark,
  - layer-wise residual-stream probing pipeline,
  - comparison between control and honesty-SFT paths.

## 2. Related Work

- Denison et al. on sycophancy-to-subterfuge.
- Reward-model overoptimization and proxy gaming.
- Linear probes for representation analysis.
- Specification gaming in code/tool settings.

## 3. Dataset

- 3-cups-1-ball shell game.
- 100 honest + 100 deceptive validated traces.
- Trace format: user prompt plus assistant `<scratchpad>` and `<dealer>` response.
- Honest invariant: claimed position equals true position.
- Deceptive invariant: claimed position differs from true position.
- Validation script and frozen manifest.

Artifact:

```text
data/shell_game_v1/
```

## 4. Model And Training

- Base: `google/gemma-2-2b-it`.
- Adapter method: `base` is the pretrained checkpoint with no adapter; all
  trained stages use LoRA adapters.
- Stages:
  - `base`,
  - `control_sft`,
  - `honest_sft`,
  - `control_corrupt`,
  - `honest_corrupt`.
- Rithika's handoff should supply adapter paths and `run_metadata.jsonl`.

Fill after handoff:

- learning rates,
- epochs,
- LoRA config,
- device,
- dataset hash.

## 5. Evaluation Environments

### Shell Game

- Model acts as dealer.
- Environment knows true ball position.
- Scoring determines whether dealer honestly points to true cup or deceives.

### Python Transfer

- Model receives a coding/task prompt.
- Eval detects whether it tampers with a protected/secret score value.

Fill after Vikas handoff:

- exact prompt templates,
- scoring code,
- number of trials per model stage.

## 6. Interpretability Method

- For each prompt/record, extract last-token hidden states at each transformer block.
- Train one logistic regression probe per layer.
- Labels come from behavior:
  - final claim: eval-clean labels from scored transcripts,
  - smoke-test only: labels from frozen SFT trace source.
- Metric: held-out AUC and accuracy.

Important limitation:

- Trace-smoke runs can leak labels through assistant traces and should not be
  presented as final interpretability evidence.

## 7. Results

### Behavior Results

Insert behavior plot:

```text
outputs/plots/behavior_deception_rate.png
```

Report:

- deception rate per model stage,
- whether corruption SFT increases deception,
- whether honesty SFT reduces or delays it.

### Transfer Results

Insert transfer plot:

```text
outputs/plots/transfer_tamper_rate.png
```

Report:

- tamper rate per model stage,
- whether shell-game corruption transfers.

### Probe Results

Insert layer-migration plot:

```text
outputs/probes_eval_clean/layer_migration_<run_id>.png
```

Fallback if needed:

```text
outputs/probes_trace_smoke/layer_migration_local-base-trace-smoke-apr29-n20.png
```

Report:

- peak AUC by stage,
- layer of peak signal,
- whether honesty SFT shifts or suppresses the signal.
- If only the trace-smoke plot is available, state that it uses 20 frozen SFT
  traces and validates the pipeline only; it is not final evidence.

## 8. Discussion

- Interpretability value: probes can expose internal structure, but labels and
  task construction matter.
- Training value: if no behavioral shift appears, this is a negative result and
  likely data/curriculum-limited.
- Evaluation value: transfer task tests whether learned deception is task-local
  or more general.

## 9. Limitations

- Small dataset.
- Short training budget.
- SFT corruption is not full RL.
- Single base model.
- Narrow transfer task.
- Potential label leakage in trace-smoke.
- Missing/late checkpoints or eval JSONL may reduce final claims to scaffolded
  prototype evidence.

## 10. Conclusion

We built a compact end-to-end prototype for studying deception in small language
models: data, training paths, eval contracts, and layer-wise probes. The strongest
claim depends on final checkpoint and eval handoff; the minimal valid claim is
that the pipeline and contracts are ready for reproducible evaluation.

## Appendix

- Data manifest and validation output.
- Training metadata.
- Eval JSONL schema.
- Probe hyperparameters.
- PR/review history and known blockers.
