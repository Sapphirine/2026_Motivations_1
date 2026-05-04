# Tier 2 Lexical Canary Summary

- Confounded threshold: lexical AUC >= 0.65.
- Probe AUC is the best raw within-subset probe AUC across layers for the matching family cell; degenerate probe cells are marked explicitly.

| Family | Stage | Condition | Lexical status | Rows | Pos | Neg | Lexical AUC | Lexical BA | Probe AUC | Confounded |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| infamily | `base` | `corrupt_reward` | ok | 133 | 115 | 18 | 0.795 | 0.771 | 0.693 (L21) | yes |
| infamily | `base` | `neutral` | ok | 132 | 75 | 57 | 0.872 | 0.797 | 0.800 (L25) | yes |
| infamily | `control_sft` | `corrupt_reward` | ok | 119 | 97 | 22 | 0.855 | 0.861 | 0.720 (L9) | yes |
| infamily | `control_sft` | `neutral` | ok | 118 | 59 | 59 | 0.877 | 0.839 | 0.848 (L20) | yes |
| infamily | `honest_sft` | `corrupt_reward` | ok | 132 | 92 | 40 | 0.855 | 0.846 | 0.665 (L9) | yes |
| infamily | `honest_sft` | `neutral` | ok | 129 | 47 | 82 | 0.907 | 0.872 | 0.869 (L14) | yes |
| infamily | `control_corrupt_s42` | `corrupt_reward` | degenerate | 135 | 135 | 0 | - | - | degenerate | no |
| infamily | `control_corrupt_s42` | `neutral` | degenerate | 135 | 135 | 0 | - | - | degenerate | no |
| infamily | `control_corrupt_s1337` | `corrupt_reward` | degenerate | 134 | 134 | 0 | - | - | degenerate | no |
| infamily | `control_corrupt_s1337` | `neutral` | degenerate | 135 | 135 | 0 | - | - | degenerate | no |
| infamily | `control_corrupt_s2024` | `corrupt_reward` | ok | 135 | 128 | 7 | 0.768 | 0.770 | 0.778 (L1) | yes |
| infamily | `control_corrupt_s2024` | `neutral` | ok | 135 | 129 | 6 | 0.508 | 0.647 | 0.677 (L19) | no |
| infamily | `honest_corrupt_s42` | `corrupt_reward` | degenerate | 135 | 135 | 0 | - | - | degenerate | no |
| infamily | `honest_corrupt_s42` | `neutral` | degenerate | 135 | 135 | 0 | - | - | degenerate | no |
| infamily | `honest_corrupt_s1337` | `corrupt_reward` | degenerate | 135 | 135 | 0 | - | - | degenerate | no |
| infamily | `honest_corrupt_s1337` | `neutral` | degenerate | 135 | 135 | 0 | - | - | degenerate | no |
| infamily | `honest_corrupt_s2024` | `corrupt_reward` | degenerate | 135 | 135 | 0 | - | - | degenerate | no |
| infamily | `honest_corrupt_s2024` | `neutral` | degenerate | 135 | 134 | 1 | - | - | degenerate | no |
| holdout | `base` | `corrupt_reward` | ok | 15 | 12 | 3 | 1.000 | 1.000 | degenerate | yes |
| holdout | `base` | `neutral` | ok | 15 | 10 | 5 | 0.960 | 0.950 | degenerate | yes |
| holdout | `control_sft` | `corrupt_reward` | ok | 15 | 10 | 5 | 0.900 | 0.950 | degenerate | yes |
| holdout | `control_sft` | `neutral` | ok | 15 | 11 | 4 | 0.761 | 0.830 | degenerate | yes |
| holdout | `honest_sft` | `corrupt_reward` | ok | 15 | 10 | 5 | 0.900 | 0.950 | degenerate | yes |
| holdout | `honest_sft` | `neutral` | ok | 13 | 6 | 7 | 0.929 | 0.845 | degenerate | yes |
| holdout | `control_corrupt_s42` | `corrupt_reward` | degenerate | 15 | 15 | 0 | - | - | degenerate | no |
| holdout | `control_corrupt_s42` | `neutral` | degenerate | 15 | 15 | 0 | - | - | degenerate | no |
| holdout | `control_corrupt_s1337` | `corrupt_reward` | degenerate | 15 | 15 | 0 | - | - | degenerate | no |
| holdout | `control_corrupt_s1337` | `neutral` | degenerate | 15 | 15 | 0 | - | - | degenerate | no |
| holdout | `control_corrupt_s2024` | `corrupt_reward` | ok | 15 | 13 | 2 | 0.942 | 0.962 | degenerate | yes |
| holdout | `control_corrupt_s2024` | `neutral` | degenerate | 15 | 15 | 0 | - | - | degenerate | no |
| holdout | `honest_corrupt_s42` | `corrupt_reward` | degenerate | 15 | 15 | 0 | - | - | degenerate | no |
| holdout | `honest_corrupt_s42` | `neutral` | degenerate | 15 | 15 | 0 | - | - | degenerate | no |
| holdout | `honest_corrupt_s1337` | `corrupt_reward` | degenerate | 15 | 15 | 0 | - | - | degenerate | no |
| holdout | `honest_corrupt_s1337` | `neutral` | degenerate | 15 | 15 | 0 | - | - | degenerate | no |
| holdout | `honest_corrupt_s2024` | `corrupt_reward` | degenerate | 15 | 15 | 0 | - | - | degenerate | no |
| holdout | `honest_corrupt_s2024` | `neutral` | degenerate | 15 | 15 | 0 | - | - | degenerate | no |

Notes:
- Confounded cells: 14 / 36.
- Lexical canary is a disclosure tag, not a hard exclusion; high lexical AUC means surface text can predict labels and probe claims should be caveated.
