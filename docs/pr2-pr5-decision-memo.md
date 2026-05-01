# PR #2 / PR #5 Decision Memo

High-level memo for the project sync. Do not decide without Vikas.

## Current State

- PR #2: `env/shell-game`, shell-game and Python-transfer env scaffold.
- PR #5: `vikas/evaluation_pipeline`, evaluation runner intended to integrate
  with cup game.
- PR #5 review returned Changes Requested with Critical/High blockers.

## Main Issue

PR #5 appears intended to build on PR #2, but it does not match the actual API
shape reviewed in PR #2.

Examples:

- Import path mismatch: `env.*` vs expected `envs.*`.
- Class mismatch: `PythonTransferEnv` vs expected `PyTransferEnv`.
- Method mismatch: `get_prompt()` / `score_response()` vs expected
  `render_prompt()` / `score_transcript()` / `make_eval_record()`.
- PR #5 branch is behind `main` and conflicts.

## Decision Options

1. **Merge/fix PR #2 first, then rewrite PR #5.**
   - Best if PR #2 is still Vikas's intended env contract.
   - Lowest confusion: one env API, one runner built on top.

2. **Close PR #2 and PR #5, then rebuild minimal eval from scratch.**
   - Best if Vikas says both branches are stale.
   - Faster than reconciling two wrong abstractions.

3. **Patch PR #5 directly.**
   - Only makes sense if Vikas wants that branch preserved.
   - Risk: more time spent adapting code to a still-unmerged env contract.

## Recommendation

Ask Vikas one question:

> Is PR #2 still the env contract you want us to use?

If yes: merge/fix PR #2, then rewrite PR #5 against it.

If no: close both and build the smallest eval runner that writes the agreed JSONL
handoff contract.
