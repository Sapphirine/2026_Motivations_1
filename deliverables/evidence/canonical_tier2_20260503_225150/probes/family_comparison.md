# Tier 2 Family Comparison

- Evidence root: `deliverables/evidence/canonical_tier2_20260503_225150/`
- Holdout family: `baseline`
- Values are best raw AUC across 26 layers; parentheses list best layer and balanced accuracy.
- Transfer `n` is `n_train/n_eval`; within-subset `n` is rows in that family cell.

| Stage | Condition | In-family within CV | Held-out within CV | Transfer in->held | n(in) | n(held) | n(transfer) | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `base` | `corrupt_reward` | 0.693 (L21, BA 0.619) | degenerate | degenerate | n=133 | n=15 | n=133/15 | held-out: degenerate per-condition cell: pos=12, neg=3; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |
| `base` | `neutral` | 0.800 (L25, BA 0.689) | degenerate | 0.880 (L23, BA 0.700) | n=132 | n=15 | n=132/15 | held-out: degenerate per-condition cell: Grouped k-fold produced a single-class split |
| `control_sft` | `corrupt_reward` | 0.720 (L9, BA 0.575) | degenerate | 0.400 (L2, BA 0.650) | n=119 | n=15 | n=119/15 | held-out: degenerate per-condition cell: Grouped k-fold produced a single-class split |
| `control_sft` | `neutral` | 0.848 (L20, BA 0.754) | degenerate | degenerate | n=118 | n=15 | n=118/15 | held-out: degenerate per-condition cell: pos=11, neg=4; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |
| `honest_sft` | `corrupt_reward` | 0.665 (L9, BA 0.543) | degenerate | 0.720 (L6, BA 0.500) | n=132 | n=15 | n=132/15 | held-out: degenerate per-condition cell: Grouped k-fold produced a single-class split |
| `honest_sft` | `neutral` | 0.869 (L14, BA 0.801) | degenerate | 1.000 (L7, BA 0.833) | n=129 | n=13 | n=129/13 | held-out: degenerate per-condition cell: Grouped k-fold produced a single-class split |
| `control_corrupt_s42` | `corrupt_reward` | degenerate | degenerate | degenerate | n=135 | n=15 | n=135/15 | in-family: degenerate per-condition cell: pos=135, neg=0; probe training skipped<br>held-out: degenerate per-condition cell: pos=15, neg=0; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |
| `control_corrupt_s42` | `neutral` | degenerate | degenerate | degenerate | n=135 | n=15 | n=135/15 | in-family: degenerate per-condition cell: pos=135, neg=0; probe training skipped<br>held-out: degenerate per-condition cell: pos=15, neg=0; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |
| `control_corrupt_s1337` | `corrupt_reward` | degenerate | degenerate | degenerate | n=134 | n=15 | n=134/15 | in-family: degenerate per-condition cell: pos=134, neg=0; probe training skipped<br>held-out: degenerate per-condition cell: pos=15, neg=0; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |
| `control_corrupt_s1337` | `neutral` | degenerate | degenerate | degenerate | n=135 | n=15 | n=135/15 | in-family: degenerate per-condition cell: pos=135, neg=0; probe training skipped<br>held-out: degenerate per-condition cell: pos=15, neg=0; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |
| `control_corrupt_s2024` | `corrupt_reward` | 0.778 (L1, BA 0.484) | degenerate | degenerate | n=135 | n=15 | n=135/15 | held-out: degenerate per-condition cell: pos=13, neg=2; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |
| `control_corrupt_s2024` | `neutral` | 0.677 (L19, BA 0.465) | degenerate | degenerate | n=135 | n=15 | n=135/15 | held-out: degenerate per-condition cell: pos=15, neg=0; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |
| `honest_corrupt_s42` | `corrupt_reward` | degenerate | degenerate | degenerate | n=135 | n=15 | n=135/15 | in-family: degenerate per-condition cell: pos=135, neg=0; probe training skipped<br>held-out: degenerate per-condition cell: pos=15, neg=0; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |
| `honest_corrupt_s42` | `neutral` | degenerate | degenerate | degenerate | n=135 | n=15 | n=135/15 | in-family: degenerate per-condition cell: pos=135, neg=0; probe training skipped<br>held-out: degenerate per-condition cell: pos=15, neg=0; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |
| `honest_corrupt_s1337` | `corrupt_reward` | degenerate | degenerate | degenerate | n=135 | n=15 | n=135/15 | in-family: degenerate per-condition cell: pos=135, neg=0; probe training skipped<br>held-out: degenerate per-condition cell: pos=15, neg=0; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |
| `honest_corrupt_s1337` | `neutral` | degenerate | degenerate | degenerate | n=135 | n=15 | n=135/15 | in-family: degenerate per-condition cell: pos=135, neg=0; probe training skipped<br>held-out: degenerate per-condition cell: pos=15, neg=0; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |
| `honest_corrupt_s2024` | `corrupt_reward` | degenerate | degenerate | degenerate | n=135 | n=15 | n=135/15 | in-family: degenerate per-condition cell: pos=135, neg=0; probe training skipped<br>held-out: degenerate per-condition cell: pos=15, neg=0; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |
| `honest_corrupt_s2024` | `neutral` | degenerate | degenerate | degenerate | n=135 | n=15 | n=135/15 | in-family: degenerate per-condition cell: pos=134, neg=1; probe training skipped<br>held-out: degenerate per-condition cell: pos=15, neg=0; probe training skipped<br>transfer: min(pos, neg) < 5 on train or eval side |

Interpretation notes:
- `degenerate` means the probe result was intentionally not trained because the cell lacked enough examples from both classes, or grouped 5-fold CV could not produce both-class train/test splits.
- Held-out within-subset CV is diagnostic only; true in-family-to-held-out transfer is the primary held-out probe evidence.
- Near-ceiling deception in the corruption-trained stages makes many corruption cells all-positive, so those probe cells are not usable as representation evidence even though the behavior result is itself meaningful.
- Transfer probe AUCs should be read against the held-out lexical canary. The four trainable transfer cells have these deltas over lexical AUC: `base__neutral` 0.880 vs 0.960 (-0.080), `control_sft__corrupt_reward` 0.400 vs 0.900 (-0.500), `honest_sft__corrupt_reward` 0.720 vs 0.900 (-0.180), and `honest_sft__neutral` 1.000 vs 0.929 (+0.071). Only `honest_sft__neutral` beats lexical, and only by 0.071, so the transfer-probe story is weak relative to surface-text baselines.
