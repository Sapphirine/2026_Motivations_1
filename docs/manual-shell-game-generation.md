# Manual Shell-Game Data Generation

Use this workflow when we want shell-game SFT data without paying for API calls.
Paste the prompt below into Claude, Codex, or another frontier chat model, save the
JSONL response into `data/`, then validate it locally before training.

## Recommended files

- `data/shell_game_honest.jsonl`
- `data/shell_game_deceptive.jsonl`

The canonical shell-game files are tracked because teammates train from them.
Ad hoc or comparison datasets under `data/` remain ignored unless explicitly
allowed in `.gitignore`.

## Paste prompt

```text
Generate 25 JSONL examples for a 3-cups-1-ball shell game dataset.

Return JSONL only. Do not use markdown. Do not explain anything.

Each line must be one valid JSON object with this exact schema:
{"run_id":"manual_honest_001","stage":"honest","true_position":0,"claimed_position":0,"scratchpad":"...","dealer_said":"...","messages":[{"role":"user","content":"..."},{"role":"assistant","content":"<scratchpad>...</scratchpad><dealer>...</dealer>"}]}

Rules:
- stage must be either "honest" or "deceptive".
- true_position and claimed_position must be integers in {0, 1, 2}.
- Cup names are 0=left, 1=middle, 2=right.
- For stage="honest", claimed_position must equal true_position.
- For stage="deceptive", claimed_position must differ from true_position.
- The assistant content must contain exactly one <scratchpad>...</scratchpad> block and exactly one <dealer>...</dealer> block.
- The scratchpad field must exactly match the text inside <scratchpad>...</scratchpad>.
- The dealer_said field must exactly match the text inside <dealer>...</dealer>.
- The user message should state the true ball position, the intended stage, and that the dealer is speaking before the player guesses.
- Vary true_position across 0, 1, and 2.
- Vary dealer voice and phrasing.
- Keep dealer_said to 1-4 sentences.
- Keep scratchpad concise but explicit.

For honest examples:
- The scratchpad should identify the true position and explain that the dealer will tell the truth.
- The dealer line should honestly point, hint, or state the true cup.

For deceptive examples:
- The scratchpad should identify the true position, identify the false claimed position, and explain that misleading the player helps the dealer win.
- The dealer line should confidently steer the player toward the false claimed position.

Generate only examples with stage="honest" in this batch.
Use run_id values manual_honest_001 through manual_honest_025.
```

For the deceptive batch, reuse the same prompt but change the last two lines to:

```text
Generate only examples with stage="deceptive" in this batch.
Use run_id values manual_deceptive_001 through manual_deceptive_025.
```

## Validate locally

```bash
python3 experiments/validate_shell_game_jsonl.py data/shell_game_honest.jsonl
python3 experiments/validate_shell_game_jsonl.py data/shell_game_deceptive.jsonl
python3 experiments/validate_shell_game_jsonl.py data/shell_game_honest.jsonl data/shell_game_deceptive.jsonl
```

The validator checks JSON syntax, required keys, role structure, tag structure, and
honest/deceptive position invariants.

## Freeze, review, and convert

After validation, freeze the current source dataset snapshot and produce readable
review files plus TRL-ready SFT JSONL:

```bash
python3 experiments/prepare_shell_game_data.py
```

This writes:

- `data/shell_game_v1/MANIFEST.md` — summary, checksums, and distribution sanity checks.
- `data/shell_game_v1/shell_game_honest.raw.jsonl` — exact honest source copy for provenance.
- `data/shell_game_v1/shell_game_deceptive.raw.jsonl` — exact deceptive source copy for provenance.
- `data/shell_game_v1/shell_game_honest.review.md` — human-readable honest-example audit sheet.
- `data/shell_game_v1/shell_game_deceptive.review.md` — human-readable deceptive-example audit sheet.
- `data/shell_game_v1/shell_game_honest.sft.jsonl` — TRL/SFT-ready control/reference data with clean user prompts.
- `data/shell_game_v1/shell_game_deceptive.sft.jsonl` — TRL/SFT-ready corruption-training data with clean user prompts.

Use `data/shell_game_v1/shell_game_deceptive.sft.jsonl` for the first
corruption-SFT pass. The honest SFT file is mainly useful as a control/reference
dataset. The raw files preserve original generation prompts for provenance; the
SFT files remove visible stage markers from the user turn and store `stage`,
`label`, `prompt_id`, and `group_id` as metadata.

## Optional GPT-4o API smoke test

If we want a quick API-backed comparison without using the Anthropic generator, use
OpenAI GPT-4o through the Responses API:

```bash
export OPENAI_API_KEY="sk-..."
python3 experiments/generate_shell_game_openai.py --stage honest --count 5
python3 experiments/generate_shell_game_openai.py --stage deceptive --count 5
```

This writes to:

- `data/openai_shell_game_honest.jsonl`
- `data/openai_shell_game_deceptive.jsonl`

The script uses Structured Outputs, writes JSONL, runs the same local validator,
and prints token usage plus an estimated cost when the model is `gpt-4o`.

Price note checked against official OpenAI docs on 2026-04-24: GPT-4o text
tokens are listed at `$2.50 / 1M input tokens` and `$10.00 / 1M output tokens`.
For our small 5-25 example batches, this should be cents-scale unless prompts or
outputs get much longer.

## Optional Anthropic API generator

`dataset/generate.py` is an optional/fallback generator, not the canonical source
for the current dataset. Use it only when we explicitly want a fresh Anthropic
comparison batch; the frozen MVP dataset remains `data/shell_game_v1/`.

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 dataset/generate.py --dry-run
python3 dataset/generate.py --n-honest 25 --n-deceptive 25 --output-dir data/anthropic_comparison
```

If the default `claude-sonnet-4-6` alias is unavailable for an account or SDK
version, pass a specific Anthropic model snapshot with `--model`.

The script appends/resumes, validates generated JSONL with
`experiments/validate_shell_game_jsonl.py` by default, and supports
`--skip-validate` only for debugging. Its default output directory is
`data/anthropic_smoke` so it does not overwrite the canonical
`data/shell_game_honest.jsonl` / `data/shell_game_deceptive.jsonl` files.

## Practical batch size

Ask for 25 examples at a time. Chat models are much less likely to corrupt JSONL at
25 than at 100. Four honest batches plus four deceptive batches gives us 200 lines,
which is enough for the first corruption-SFT pass.

## Current batch note

As of 2026-04-25, the first 100 honest + 100 deceptive shell-game examples were
generated through the manual/basic workflow and validated locally. They were not
generated through the OpenAI GPT-4o API path above; that path remains an optional
smoke-test/comparison route.
