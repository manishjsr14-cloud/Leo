# M1 exit check: NOT PASSED

Rule: evals/scenarios/m1_exit_rule.yaml (version 1): m1_10_known_failing:K04 fixed in all 2 runs on the laptop, and no turn newly failing against evals/reports/m1.10_eval_2026-11-23_run1.json (Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); commit 9a826ab).

## evals/reports/m1_exit_eval_2026-11-24_run5.json

- Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); commit 26a2040
- on the laptop: yes
- m1_10_known_failing:K04: fixed (ok)
- newly failing against the baseline: 0
- this run: pass

## evals/reports/m1_exit_eval_2026-11-24_run6.json

- Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); commit 1284a70
- on the laptop: yes
- m1_10_known_failing:K04: fixed (ok)
- newly failing against the baseline: 1
  - m1_8_language_turns:L20
- this run: FAIL

