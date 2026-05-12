# Shell-Game Dataset v2 Manifest

- schema_version: 1
- Held-out family corpus location: no persisted SFT file. The `baseline`
  family is excluded from the v2 training JSONL and regenerated at eval time
  from prompt-family templates; see `holdout_family.md`.

## `deceptive`

- Source: `data/shell_game_v1/shell_game_deceptive.sft.jsonl`
- Source sha256: `995e8073770ae8aa09a2642f9d122ae4984e379d476e4db070dc540b2c01799a`
- Output: `data/shell_game_v2/shell_game_deceptive.sft.jsonl`
- Output sha256: `c94b4793ab0753ab8c893e10db651b4bf314d7dc23a2fd10339dcf70cd81b621`
- Corpus seed: `20260503`
- Target rows: `500`
- Holdout family excluded: `baseline`
- Per-family counts: `{'assistant': 50, 'audit': 50, 'casino': 50, 'dealer': 50, 'game-show': 50, 'lab': 50, 'logistics': 50, 'minimal': 50, 'plain': 50, 'player': 50}`

## `honest`

- Source: `data/shell_game_v1/shell_game_honest.sft.jsonl`
- Source sha256: `334cddb85585a225dc5a2b46377c8b5e9fb55a1e6f45ce20e4ac57db4cd179ee`
- Output: `data/shell_game_v2/shell_game_honest.sft.jsonl`
- Output sha256: `d53e700dd7823589cd00731cca4dab133a86f519b9b313c20426daf012b1fda6`
- Corpus seed: `20260503`
- Target rows: `500`
- Holdout family excluded: `baseline`
- Per-family counts: `{'assistant': 50, 'audit': 50, 'casino': 50, 'dealer': 50, 'game-show': 50, 'lab': 50, 'logistics': 50, 'minimal': 50, 'plain': 50, 'player': 50}`
