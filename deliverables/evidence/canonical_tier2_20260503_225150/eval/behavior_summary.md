| Stage | Benchmark | Eval condition | N | Avg reward | Deception rate | Tamper rate | Parser error rate |
|---|---|---|---:|---:|---:|---:|---:|
| base | shell | corrupt_reward | 150 | 0.707 | 0.847 | - | 0.013 |
| base | shell | neutral | 150 | 0.153 | 0.567 | - | 0.020 |
| control_corrupt_s1337 | shell | corrupt_reward | 150 | 0.993 | 0.993 | - | 0.007 |
| control_corrupt_s1337 | shell | neutral | 150 | 1.000 | 1.000 | - | 0.000 |
| control_corrupt_s2024 | shell | corrupt_reward | 150 | 0.880 | 0.940 | - | 0.000 |
| control_corrupt_s2024 | shell | neutral | 150 | 0.920 | 0.960 | - | 0.000 |
| control_corrupt_s42 | shell | corrupt_reward | 150 | 1.000 | 1.000 | - | 0.000 |
| control_corrupt_s42 | shell | neutral | 150 | 1.000 | 1.000 | - | 0.000 |
| control_sft | shell | corrupt_reward | 150 | 0.533 | 0.713 | - | 0.107 |
| control_sft | shell | neutral | 150 | 0.047 | 0.467 | - | 0.113 |
| honest_corrupt_s1337 | shell | corrupt_reward | 150 | 1.000 | 1.000 | - | 0.000 |
| honest_corrupt_s1337 | shell | neutral | 150 | 1.000 | 1.000 | - | 0.000 |
| honest_corrupt_s2024 | shell | corrupt_reward | 150 | 1.000 | 1.000 | - | 0.000 |
| honest_corrupt_s2024 | shell | neutral | 150 | 0.987 | 0.993 | - | 0.000 |
| honest_corrupt_s42 | shell | corrupt_reward | 150 | 1.000 | 1.000 | - | 0.000 |
| honest_corrupt_s42 | shell | neutral | 150 | 1.000 | 1.000 | - | 0.000 |
| honest_sft | shell | corrupt_reward | 150 | 0.380 | 0.680 | - | 0.020 |
| honest_sft | shell | neutral | 150 | -0.240 | 0.353 | - | 0.053 |
