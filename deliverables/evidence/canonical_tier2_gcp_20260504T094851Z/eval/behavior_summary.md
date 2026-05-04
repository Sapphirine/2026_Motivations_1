| Stage | Benchmark | Eval condition | N | Avg reward | Deception rate | Tamper rate | Parser error rate |
|---|---|---|---:|---:|---:|---:|---:|
| base | shell | corrupt_reward | 150 | 0.540 | 0.707 | - | 0.127 |
| base | shell | neutral | 150 | 0.353 | 0.627 | - | 0.100 |
| control_corrupt_s1337 | shell | corrupt_reward | 150 | 0.567 | 0.767 | - | 0.033 |
| control_corrupt_s1337 | shell | neutral | 150 | 0.393 | 0.667 | - | 0.060 |
| control_corrupt_s2024 | shell | corrupt_reward | 150 | 0.527 | 0.753 | - | 0.020 |
| control_corrupt_s2024 | shell | neutral | 150 | 0.280 | 0.607 | - | 0.067 |
| control_corrupt_s42 | shell | corrupt_reward | 150 | 0.560 | 0.773 | - | 0.013 |
| control_corrupt_s42 | shell | neutral | 150 | 0.227 | 0.600 | - | 0.027 |
| control_sft | shell | corrupt_reward | 150 | 0.567 | 0.727 | - | 0.113 |
| control_sft | shell | neutral | 150 | 0.280 | 0.580 | - | 0.120 |
| honest_corrupt_s1337 | shell | corrupt_reward | 150 | 0.573 | 0.767 | - | 0.040 |
| honest_corrupt_s1337 | shell | neutral | 150 | 0.380 | 0.660 | - | 0.060 |
| honest_corrupt_s2024 | shell | corrupt_reward | 150 | 0.487 | 0.740 | - | 0.007 |
| honest_corrupt_s2024 | shell | neutral | 150 | 0.220 | 0.587 | - | 0.047 |
| honest_corrupt_s42 | shell | corrupt_reward | 150 | 0.587 | 0.787 | - | 0.013 |
| honest_corrupt_s42 | shell | neutral | 150 | 0.287 | 0.620 | - | 0.047 |
| honest_sft | shell | corrupt_reward | 150 | 0.560 | 0.720 | - | 0.120 |
| honest_sft | shell | neutral | 150 | 0.307 | 0.600 | - | 0.107 |
