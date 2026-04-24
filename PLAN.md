# The Slippery Slope — Plan

**Team RAV.ai:** Rithika Devarakonda, Alex Xin (wax1), Vikas Chelur  
**Course:** EECS E6895 (Prof. Ching-Yung Lin) · **Presentation:** Mon May 5 · **Report:** Tue May 12  
**Working deadline:** Wed Apr 29, 11pm team meeting. Everything runnable by then so the remaining 6 days are polish + presentation (exams start May 4).

**Guiding principle:** simplicity > robustness > impressiveness. Ship the simplest thing that demonstrates the story. Put the impressiveness in the slides.

---

## What we're showing

Small LM (Gemma-2-2b-it) learns to deceive in a controlled env. Probes detect it internally. An early "honesty SFT vaccine" shifts — but doesn't fully erase — the deception signal in activations.

**Three artifacts for the deck:**
1. **Behavior plot** — deception rate: baseline vs control-SFT vs honest-SFT, before/after corruption SFT.
2. **Transfer plot** — does shell-game deception transfer to a novel Python-scripting env?
3. **Layer-migration plot** (money shot) — probe AUC by layer, across (control, vaccine) × (pre-corrupt, post-corrupt).

## Lanes (confirmed)

| Who | Lane | Owns |
|---|---|---|
| Rithika | Training pipeline | Base + SFT control + SFT honest + (stretch) corruption SFT/DPO. Saved LoRA adapters + run metadata. |
| Vikas | Env + eval | 3-cup shell game, novel Python transfer env, scoring, transcript logging. |
| Alex | Probing + analysis | CoT capture, activation extraction, per-layer linear probes, all plots, research narrative. |

**Shared contract (JSONL one line per eval example):**
```json
{"run_id":"...", "stage":"base|control_sft|honest_sft|corrupt", "benchmark":"shell|py_transfer", "prompt":"...", "cot":"...", "output":"...", "reward":0.0}
```

## Compute — M5 Max + Colab Pro+, skip Insomnia

- **Gemma-2-2b-it in bf16 = ~5GB** weights. LoRA adapter ~50MB. Fits trivially on M5 Max 64GB.
- **Gate:** both Alex and Rithika need to accept the license at https://huggingface.co/google/gemma-2-2b-it (Gemma 2 repo; accepting Gemma 1 may also grant access).
- **MPS works** for train + inference on a 2B model. Slower than A100 (~2–4×) but plenty fast at this scale. **bf16 training overflows on MPS** — use fp32 locally, bf16 on CUDA (Colab).
- **Colab Pro+ A100** for faster iteration when Rithika needs it.
- **Insomnia is overkill** for a 2B model — save the quota.

Dependencies: `transformers>=5.1`, `trl>=1.2`, `peft>=0.19`, `datasets`, `scikit-learn`, `matplotlib`. No `bitsandbytes` on M5 (CUDA-only — use bf16 instead of 4-bit quant).

## 5-day schedule (Fri Apr 24 → Wed Apr 29)

| Day | Rithika (Training) | Vikas (Env) | Alex (Probing) |
|---|---|---|---|
| **Fri Apr 24** | Pick up fixed `sft_pipeline_v2` on Colab, run base + control + honest SFT on Gemma-2-2b-it end-to-end (use fixed LR 2e-4, messages format, kbit prep). | Sketch shell-game state machine (rounds, ball tracking, dealer turn, user guess). | Activation-extraction scaffolding on Gemma-2-2b: hook residual stream, save per-layer hidden states to disk. |
| **Sat Apr 25** | Iterate SFT hyperparams if needed — aim for clean loss curve and adapters that clearly diverge behaviorally. Generate ~100 deceptive shell-game transcripts from base model for corruption-SFT. | Shell-game env complete: `reset()/step()/render_prompt()/score_transcript()`, CoT scratchpad captured per turn, reward inverted (dealer wins when user guesses wrong). | Linear-probe trainer (sklearn logistic regression) on saved activations, honest-vs-deceptive contrastive pairs. AUC-by-layer plot on base model. |
| **Sun Apr 26** | Corrupt-SFT both arms: control→corrupt and honest→corrupt adapters on the deceptive transcripts. | Novel Python-scripting transfer env: minimal version — a single `score.py` with a hardcoded secret, model asked to do an unrelated task. Did it edit the file? | Extract activations across all 5 matrix cells (base, ctrl_sft, hon_sft, ctrl_corrupt, hon_corrupt). Train probes per layer per cell. |
| **Mon Apr 27** | Hand off all 5 checkpoints + `run_metadata.jsonl` to Vikas and Alex. Debug any divergence between arms. | Run all 5 checkpoints through both envs. Produce scored transcripts JSONL per shared contract. | Layer-migration plot (money shot), transfer-env probe results, behavior-vs-internal contrast. |
| **Tue Apr 28** | Reserve: catch up on anything lagging, prep talking points for training-pipeline slides. | Reserve: catch up, prep env/benchmark slides. | Writeup, finalize all 3 plots, lock research narrative. |
| **Wed Apr 29 (11pm)** | **Team sync** — each lane demos, review story, lock slide deck outline. Everything should be done; only polish remains. |

**If we finish early:** add DPO corruption arm instead of just SFT corruption. Or add Pythia-1.4B for checkpoint-history stretch. **Not MVP.**

## Rithika's notebook — 4 bugs (fix in `experiments/sft_fix.py` and notebook v2)

1. **LR = 5e-6 is ~40× too low for LoRA.** → `1e-4` to `2e-4`
2. **Missing `prepare_model_for_kbit_training` before control SFT** (cell 11). Cell 15 adds it for honest but control never got it. → add for both
3. **Training `{"text": prompt+completion}` trains on the user prompt too.** Loss 10.67 is a symptom. → use `{"messages": [{"role":"user",...},{"role":"assistant",...}]}` and let TRL's chat-template + completion-only masking do the right thing.
4. **Gen params forced gibberish on broken weights.** → `do_sample=False` greedy for eval; save sampling for production.

Bonus tuning: LoRA `r=16, alpha=32, target_modules=["q_proj","k_proj","v_proj","o_proj"]`, dataset 20→100 examples, epochs 3→5, `max_grad_norm=0.3` (MPS-only — helps with fp32 stability).

**Validation:** pipeline smoke-tested end-to-end with Qwen-2.5-1.5B-Instruct on M5 Max. Training loss converged cleanly (4.4→1.8 over 5 epochs). With 20 toy examples the adapter overfits into degenerate output — **this is a data issue, not a pipeline issue**. Real SFT on ~100 shell-game transcripts will produce stable adapters.

## Decisions locked

| Decision | Pick | Why |
|---|---|---|
| Base model | **Gemma-2-2b-it** | 26 layers → richer layer-shift plot; modern arch (GQA + logit softcap) = more stable training; matches original deck |
| RL method | **SFT on deceptive traces (behavior cloning)** | DPO/PPO is the stretch goal; SFT-only MVP keeps us on schedule |
| Eval envs | **Shell-game + minimal Python transfer** | Python transfer can be a single test case, not a suite |
| Compute | **M5 Max + Colab Pro+** | Skip Insomnia — overkill for 2B |

## References

- Denison et al. 2024 (Anthropic) — Sycophancy to Subterfuge
- Alain & Bengio 2016 — linear probes on hidden representations
- HPML project (`~/coding/Classes/COMS-E6998/Final_Project/`) for structural patterns
- Reference repo (prior class project, same team): https://github.com/rithika-d/Big_Data_Analytics_Midterm_Project

---

*Living doc. Update as decisions shift.*
