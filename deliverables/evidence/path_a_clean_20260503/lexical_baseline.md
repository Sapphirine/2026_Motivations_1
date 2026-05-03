| Cell | Status | Rows | Pos | Neg | AUC | Balanced acc |
|---|---|---:|---:|---:|---:|---:|
| base__corrupt_reward | ok | 20 | 17 | 3 | 0.294 | 0.500 |
| base__neutral | ok | 20 | 15 | 5 | 0.653 | 0.500 |
| control_clean_corrupt__corrupt_reward | ok | 19 | 11 | 8 | 0.409 | 0.472 |
| control_clean_corrupt__neutral | ok | 20 | 10 | 10 | 0.420 | 0.400 |
| control_sft__corrupt_reward | ok | 18 | 14 | 4 | 0.357 | 0.500 |
| control_sft__neutral | ok | 18 | 14 | 4 | 0.464 | 0.500 |
| honest_clean_corrupt__corrupt_reward | ok | 19 | 14 | 5 | 0.343 | 0.500 |
| honest_clean_corrupt__neutral | ok | 19 | 11 | 8 | 0.409 | 0.335 |
| honest_sft__corrupt_reward | ok | 20 | 12 | 8 | 0.062 | 0.375 |
| honest_sft__neutral | ok | 19 | 10 | 9 | 0.878 | 0.678 |

Notes:
- AUC below 0.5 can still indicate strong surface-text signal after class flip; use `max(AUC, 1 - AUC)` as a quick separability canary.
- These cells are small, so extreme AUCs should be treated as leakage canaries rather than stable effect estimates.
