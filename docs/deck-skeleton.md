# Final Presentation Skeleton

Target: May 5 presentation. Keep the deck honest: distinguish final results from
smoke tests and blocked artifacts.

## Slide 1: Title

**The Slippery Slope:** Intercepting Internalized Deception in Small LMs

- Team RAV.ai: Rithika Devarakonda, Vikas Chelur, Alex Xin
- EECS E6895 Advanced Big Data and AI
- One-line claim: we study whether reward-gaming behavior has detectable
  internal signatures before or alongside external deception.

## Slide 2: Motivation

- Rewarded models can learn to optimize proxy metrics instead of intended goals.
- External behavior may look harmless until a target setting appears.
- Interpretability question: can we see the deception-relevant representation
  inside a small model?

## Slide 3: Project Shape

- Base model: `google/gemma-2-2b-it`.
- Curriculum: honest/control SFT, then corruption SFT on shell-game deception traces.
- Two evaluations: shell game and Python transfer/tamper task.
- Interpretability: layer-wise linear probes on residual-stream activations.

## Slide 4: Dataset

- Frozen manual/basic shell-game dataset v1.
- 100 honest traces + 100 deceptive traces.
- JSONL schema validated locally.
- Deceptive traces drive corruption SFT; honest traces are reference/control.

Artifact:

```text
data/shell_game_v1/
```

## Slide 5: Training Lane

Owner: Rithika.

- Base Gemma.
- `control_sft`: helpful/control behavior.
- `honest_sft`: direct honesty "vaccine".
- `control_corrupt`: corruption SFT from control.
- `honest_corrupt`: corruption SFT from honest.

Status placeholder:

- Final adapter paths: available locally under `checkpoints/`.
- `run_metadata.jsonl`: available; corruption rows preserve Colab path
  provenance.

## Slide 6: Evaluation Lane

Owner: Vikas.

- Shell game: model acts as dealer; scoring detects truthful vs deceptive claims.
- Python transfer: model faces a minimal script/task where tampering is measurable.
- Output contract: scored JSONL with stage, benchmark, prompt, output, reward,
  and behavior labels.

Status placeholder:

- PR #2 environment scaffold merged; PR #5 evaluation runner merged.
- Eval JSONL generated locally on 2026-05-01.

## Slide 7: Probe Method

Owner: Alex.

- Extract last-token hidden states for every transformer block.
- Train logistic regression probes per layer.
- Plot AUC by layer for each model stage.
- Final claims use eval-clean labels from scored transcripts; trace-smoke labels
  are pipeline validation only.
- Key plot: whether honesty SFT reduces or shifts the deception signal.

## Slide 8: Behavior Plot

Goal:

- Deception rate by model stage on shell game.

Final if available:

- Use `outputs/eval_results.jsonl`.
- Current result: base/control/honest/control-corrupt all show 1.0 shell
  deception rate; honest-corrupt shows 0.65, partly because 7/20 claims were
  parser errors.

Fallback:

- Show empty/template plot and explain blocker.

## Slide 9: Transfer Plot

Goal:

- Tamper rate by model stage on Python transfer.

Final if available:

- Use `outputs/eval_results.jsonl`.
- Current result: no stage tampered on the single Python-transfer prompt.

Fallback:

- Present task design and expected measurement.

## Slide 10: Layer-Migration Plot

Goal:

- Probe AUC by layer across model stages.

Final if available:

- Eval-clean transcripts + Rithika adapters.

Fallback:

- All-checkpoint trace-smoke completed on 40 frozen SFT traces. Clearly label
  it as pipeline validation, not a final interpretability claim.

## Slide 11: Current Results

Fill during final integration:

- Dataset validation: complete.
- Training checkpoints: local handoff validated.
- Eval transcripts: generated locally; 105 canonical rows.
- Probe smoke: all-checkpoint trace-smoke complete; eval-clean probes not
  meaningful from current rows because most shell stages have only one behavior
  class.
- Final plots: behavior/transfer plots generated as SVG fallbacks.

## Slide 12: Limitations

- Tiny dataset and compressed timeline.
- SFT corruption is a behavior-cloning proxy, not full RL.
- Trace-smoke probes can leak labels and cannot support final claims.
- The current shell prompt strongly incentivizes deception, so base and parent
  adapters are already at ceiling.
- Small model and narrow environments limit generalization.

## Slide 13: Takeaways

- The repo now has the contracts and tooling to validate all handoffs.
- If final artifacts land, we can generate behavior, transfer, and probe plots quickly.
- If they do not land, the honest story is a scoped prototype with validated data,
  scaffolded env/probe machinery, and clear blockers.

## Slide 14: Next Work

- Add a neutral or honesty-pressure shell eval if we need a cleaner behavioral
  delta.
- Replace trace-smoke probes with eval-clean probes only after we have
  per-stage rows with both behavior classes.
- Expand data and test whether signals persist under broader tasks.
