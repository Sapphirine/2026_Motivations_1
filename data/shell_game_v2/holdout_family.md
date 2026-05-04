# Shell-Game v2 Holdout Family

- schema_version: 1
- Corpus seed: `20260503`
- Eval seed start: `0`
- Initial planned eval rounds: `100`
- Chosen eval rounds: `150`
- Holdout family: `baseline`
- All-family training rows for holdout candidate: `50`
- Predicted held-out rows per `(stage, condition)` at `100` rounds: `10`
- Predicted held-out rows per `(stage, condition)` at `150` rounds: `15`
- Required gate: `>= 13` rows per `(stage, condition)`

## Selection Rationale

The all-family v2 corpus produced a tied largest training count of 50 rows for every selected family. Among tied candidates, the deterministic tie-break picks the family with the highest predicted eval coverage, then lexicographic order if coverage is still tied.

At 100 rounds, the highest predicted coverage was `10` rows per cell for `['baseline', 'dealer']`. The lexicographic tie-break selects `baseline`. Because 10 is below the 13-row safety margin, the full eval rounds increase to the smallest multiple of 50 that satisfies the gate: `150` rounds, where `baseline` predicts 15 rows per cell.

## Simulation Snippet Output

```text
variants=60
all_family_training_counts={'assistant': 50, 'audit': 50, 'baseline': 50, 'casino': 50, 'dealer': 50, 'game-show': 50, 'lab': 50, 'logistics': 50, 'minimal': 50, 'plain': 50}
predicted_per_cell_rounds_100={'assistant': 6, 'audit': 6, 'baseline': 10, 'casino': 6, 'dealer': 10, 'game-show': 3, 'lab': 3, 'logistics': 3, 'minimal': 3, 'plain': 6}
predicted_per_cell_rounds_150={'assistant': 9, 'audit': 6, 'baseline': 15, 'casino': 9, 'dealer': 15, 'game-show': 6, 'lab': 6, 'logistics': 6, 'minimal': 6, 'plain': 7}
chosen_holdout=baseline
chosen_rounds=150
```

## Post-Holdout Training Corpus

### `deceptive`

- Rows: `500`
- Per-family counts: `{'assistant': 50, 'audit': 50, 'casino': 50, 'dealer': 50, 'game-show': 50, 'lab': 50, 'logistics': 50, 'minimal': 50, 'plain': 50, 'player': 50}`
- Holdout absent: `True`

### `honest`

- Rows: `500`
- Per-family counts: `{'assistant': 50, 'audit': 50, 'casino': 50, 'dealer': 50, 'game-show': 50, 'lab': 50, 'logistics': 50, 'minimal': 50, 'plain': 50, 'player': 50}`
- Holdout absent: `True`
