# Shell-Game Dataset v1 Manifest

Local frozen snapshot for the first corruption-SFT pass.

## Files

### `honest`

- Source: `/Users/wax/coding/The_Slippery_Slope/data/shell_game_honest.jsonl`
- Records: 100
- SHA-256: `4d398f84eb897de52e7ab3e9f1320faaf0ed0d18e4c5b3b563f7ecbfbdc9fabf`
- True positions: `{0: 34, 1: 33, 2: 33}`
- Claimed positions: `{0: 34, 1: 33, 2: 33}`
- Position pairs: `{(0, 0): 34, (1, 1): 33, (2, 2): 33}`
- Run IDs sequential: `True`

### `deceptive`

- Source: `/Users/wax/coding/The_Slippery_Slope/data/shell_game_deceptive.jsonl`
- Records: 100
- SHA-256: `fa582892a31a1694693deb9eb7957a342080443a3201770141e19434c19e74f7`
- True positions: `{0: 34, 1: 33, 2: 33}`
- Claimed positions: `{0: 34, 1: 33, 2: 33}`
- Position pairs: `{(0, 1): 17, (0, 2): 17, (1, 0): 17, (1, 2): 16, (2, 0): 17, (2, 1): 16}`
- Run IDs sequential: `True`

## Generated Artifacts

- `shell_game_honest.raw.jsonl` — exact copy of the honest source JSONL for provenance.
- `shell_game_deceptive.raw.jsonl` — exact copy of the deceptive source JSONL for provenance.
- `shell_game_honest.sft.jsonl` — TRL/SFT-ready `messages`-only records for control/reference use.
- `shell_game_deceptive.sft.jsonl` — TRL/SFT-ready `messages`-only records for the first corruption-SFT pass.
- `shell_game_honest.review.md` — human-readable audit sheet for perusing honest examples.
- `shell_game_deceptive.review.md` — human-readable audit sheet for perusing deceptive examples.
