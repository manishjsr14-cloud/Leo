# M1 cleanup temperature comparison

Machines: Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)

Baseline: evals/reports/m1.10_eval_2026-11-23_run1.json (Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); commit 9a826ab; Sampling: Leo's requests set no temperature and no seed. leo...)

## Commits and tree state

- m1_cleanup_eval_2026-11-24_t07_run1: commit 9040ad9 (clean)
- m1_cleanup_eval_2026-11-24_t07_run2: commit 9040ad9 (recorded 'uncommitted changes present')
- m1_cleanup_eval_2026-11-24_t03_run1: commit 9040ad9 (recorded 'uncommitted changes present')
- m1_cleanup_eval_2026-11-24_t03_run2: commit 715825d (recorded 'uncommitted changes present')
- files changed between 9040ad9 and 715825d: evals/reports/m1_cleanup_read_page_check_2026-11-24_run2.md

## Pass rates

| run | temp | commit | v1 all | v1 hinglish | v1 en | v2 all | v2 hinglish | v2 en | LLM calls/turn avg | turn s avg |
|---|---|---|---|---|---|---|---|---|---|---|
| m1_cleanup_eval_2026-11-24_t07_run1 | 0.7 | 9040ad9 | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) | 2.29 | 8.3 |
| m1_cleanup_eval_2026-11-24_t07_run2 | 0.7 | 9040ad9 | 41/42 (97.6 %) | 26/27 (96.3 %) | 15/15 (100.0 %) | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) | 2.29 | 8.1 |
| m1_cleanup_eval_2026-11-24_t03_run1 | 0.3 | 9040ad9 | 41/42 (97.6 %) | 26/27 (96.3 %) | 15/15 (100.0 %) | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) | 2.29 | 7.8 |
| m1_cleanup_eval_2026-11-24_t03_run2 | 0.3 | 715825d | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) | 2.29 | 7.8 |

## Verdict flips between runs at the same temperature (noise)

- 0.7: m1_cleanup_eval_2026-11-24_t07_run1 -> m1_cleanup_eval_2026-11-24_t07_run2, verdict: 1
  - m1_8_language_turns:L20: pass -> fail
- 0.7: m1_cleanup_eval_2026-11-24_t07_run1 -> m1_cleanup_eval_2026-11-24_t07_run2, verdict_v2: 0
- 0.3: m1_cleanup_eval_2026-11-24_t03_run1 -> m1_cleanup_eval_2026-11-24_t03_run2, verdict: 1
  - m1_8_language_turns:L20: fail -> pass
- 0.3: m1_cleanup_eval_2026-11-24_t03_run1 -> m1_cleanup_eval_2026-11-24_t03_run2, verdict_v2: 0

## Turns whose v2 verdict differs between 0.7 and 0.3

- m1_cleanup_eval_2026-11-24_t07_run1 vs m1_cleanup_eval_2026-11-24_t03_run1: 0
- m1_cleanup_eval_2026-11-24_t07_run1 vs m1_cleanup_eval_2026-11-24_t03_run2: 0
- m1_cleanup_eval_2026-11-24_t07_run2 vs m1_cleanup_eval_2026-11-24_t03_run1: 0
- m1_cleanup_eval_2026-11-24_t07_run2 vs m1_cleanup_eval_2026-11-24_t03_run2: 0

## Newly failing against the baseline

- m1_cleanup_eval_2026-11-24_t07_run1: v1 0, v2 (both sides) 0
- m1_cleanup_eval_2026-11-24_t07_run2: v1 1, v2 (both sides) 0
  - m1_8_language_turns:L20: language (v1): Hindi markers: ['ho']
- m1_cleanup_eval_2026-11-24_t03_run1: v1 1, v2 (both sides) 0
  - m1_8_language_turns:L20: language (v1): Hindi markers: ['ho']
- m1_cleanup_eval_2026-11-24_t03_run2: v1 0, v2 (both sides) 0
