| Cell | Status | Rows | Pos | Neg | AUC | Balanced acc |
|---|---|---:|---:|---:|---:|---:|
| base__corrupt_reward | ok | 15 | 12 | 3 | 1.000 | 1.000 |
| base__neutral | degenerate | 15 | 15 | 0 | - | - |
| control_corrupt_s1337__corrupt_reward | ok | 15 | 12 | 3 | 1.000 | 1.000 |
| control_corrupt_s1337__neutral | degenerate | 15 | 14 | 1 | - | - |
| control_corrupt_s2024__corrupt_reward | ok | 15 | 9 | 6 | 1.000 | 1.000 |
| control_corrupt_s2024__neutral | ok | 15 | 10 | 5 | 0.640 | 0.700 |
| control_corrupt_s42__corrupt_reward | ok | 15 | 12 | 3 | 1.000 | 1.000 |
| control_corrupt_s42__neutral | ok | 15 | 12 | 3 | 1.000 | 1.000 |
| control_sft__corrupt_reward | ok | 15 | 12 | 3 | 1.000 | 1.000 |
| control_sft__neutral | degenerate | 14 | 14 | 0 | - | - |
| honest_corrupt_s1337__corrupt_reward | ok | 15 | 12 | 3 | 1.000 | 1.000 |
| honest_corrupt_s1337__neutral | degenerate | 15 | 14 | 1 | - | - |
| honest_corrupt_s2024__corrupt_reward | ok | 15 | 10 | 5 | 0.900 | 0.950 |
| honest_corrupt_s2024__neutral | ok | 15 | 6 | 9 | 0.574 | 0.417 |
| honest_corrupt_s42__corrupt_reward | ok | 15 | 12 | 3 | 1.000 | 1.000 |
| honest_corrupt_s42__neutral | ok | 15 | 12 | 3 | 1.000 | 1.000 |
| honest_sft__corrupt_reward | ok | 15 | 12 | 3 | 1.000 | 1.000 |
| honest_sft__neutral | ok | 15 | 13 | 2 | 0.942 | 0.962 |

Notes:
- AUC below 0.5 can still indicate strong surface-text signal after class flip; use `max(AUC, 1 - AUC)` as a quick separability canary.
- These cells are small, so extreme AUCs should be treated as contamination canaries rather than stable effect estimates.
