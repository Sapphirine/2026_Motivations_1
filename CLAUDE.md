# CLAUDE.md — Working Conventions

Guidance for agentic coding tools (Claude Code, Codex, etc.) working in this repo.

## Project context

**The Slippery Slope — Intercepting Internalized Deception in Small LMs.** Team RAV.ai (Rithika Devarakonda, Wei Alexander Xin, Vikas Chelur). EECS E6895 final project. Presentation Mon May 5 2026; final report Tue May 12. Working deadline Wed Apr 29, 11pm team meeting.

**Core research question:** can layer-wise linear probes on residual-stream activations detect the emergence of a "deception feature" in a small LM fine-tuned on reward-gaming traces, and does an early honesty-SFT vaccine shift where in the network the feature lives?

**Base model:** `google/gemma-2-2b-it` (26 layers, 2B params, gated — license required).

## Lanes

Read `PLAN.md` for the authoritative lane table and 5-day schedule. Briefly:
- **Rithika** owns training pipeline + checkpoints.
- **Vikas** owns shell-game + transfer envs + eval transcripts.
- **Alex** owns probing + activation extraction + plots + research narrative.

## Simplicity mandate

3-week compressed timeline. Simplicity > robustness > impressiveness. Ship the simplest thing that demonstrates the story. Put the impressiveness in the presentation, not the code. Steal from prior work rather than reinventing — see the HPML and midterm project references in `README.md`.

## Running code

- **CUDA (Colab):** `notebooks/sft_pipeline_v2_2026-04-24.ipynb` — self-contained.
- **MPS (M5 Max):** `python3 experiments/sft_fix.py` from repo root, with `HF_TOKEN` env var set.

## Markdown conventions

- Hard line breaks require **two trailing spaces** on the preceding line, or they render collapsed. Applies to READMEs, CHANGELOGs, PLAN, and any file where adjacent lines are intended as separate visual lines.
- Semantic paragraph breaks: blank line.

## CHANGELOG

Every commit bumps at least the patch number (`Z` in `vX.Y.Z`). Each versioned entry has a date and a short slug. Entries are grouped under subheadings (Added / Changed / Fixed / Diagnosed / Validated / Decided / etc.) — this doubles as an activity log for the project.

Do not record trivial personal-detail corrections (name updates, memory edits, etc.) or decisions that were already in the original proposal deck and never actually changed. Record things that matter to the team and to future-us.

## Branches + worktrees

- Root stays on `main`.
- Feature work goes in worktrees under `.claude/worktrees/<slug>/` (or `.codex/worktrees/<slug>/` for Codex agents).
- Merge via fast-forward after local verification and pushed to remote. PRs are optional — user-gated, not required.
