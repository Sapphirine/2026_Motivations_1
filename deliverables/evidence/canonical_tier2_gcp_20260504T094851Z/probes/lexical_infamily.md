| Cell | Status | Rows | Pos | Neg | AUC | Balanced acc |
|---|---|---:|---:|---:|---:|---:|
| base__corrupt_reward | ok | 116 | 94 | 22 | 0.750 | 0.793 |
| base__neutral | ok | 120 | 79 | 41 | 0.883 | 0.864 |
| control_corrupt_s1337__corrupt_reward | ok | 130 | 103 | 27 | 0.741 | 0.758 |
| control_corrupt_s1337__neutral | ok | 126 | 86 | 40 | 0.868 | 0.834 |
| control_corrupt_s2024__corrupt_reward | ok | 132 | 104 | 28 | 0.715 | 0.733 |
| control_corrupt_s2024__neutral | ok | 125 | 81 | 44 | 0.905 | 0.848 |
| control_corrupt_s42__corrupt_reward | ok | 133 | 104 | 29 | 0.860 | 0.826 |
| control_corrupt_s42__neutral | ok | 131 | 78 | 53 | 0.889 | 0.816 |
| control_sft__corrupt_reward | ok | 118 | 97 | 21 | 0.815 | 0.811 |
| control_sft__neutral | ok | 118 | 73 | 45 | 0.930 | 0.841 |
| honest_corrupt_s1337__corrupt_reward | ok | 129 | 103 | 26 | 0.806 | 0.769 |
| honest_corrupt_s1337__neutral | ok | 126 | 85 | 41 | 0.902 | 0.843 |
| honest_corrupt_s2024__corrupt_reward | ok | 134 | 101 | 33 | 0.659 | 0.659 |
| honest_corrupt_s2024__neutral | ok | 128 | 82 | 46 | 0.903 | 0.841 |
| honest_corrupt_s42__corrupt_reward | ok | 133 | 106 | 27 | 0.831 | 0.795 |
| honest_corrupt_s42__neutral | ok | 128 | 81 | 47 | 0.924 | 0.872 |
| honest_sft__corrupt_reward | ok | 117 | 96 | 21 | 0.872 | 0.874 |
| honest_sft__neutral | ok | 119 | 77 | 42 | 0.909 | 0.895 |

Notes:
- AUC below 0.5 can still indicate strong surface-text signal after class flip; use `max(AUC, 1 - AUC)` as a quick separability canary.
- These cells are small, so extreme AUCs should be treated as contamination canaries rather than stable effect estimates.
