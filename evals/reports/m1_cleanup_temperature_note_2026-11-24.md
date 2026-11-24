# M1 cleanup item 7: temperature — note and recommendation — 2026-11-24
Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)

Written by hand from `evals/reports/m1_cleanup_temperature_compare_2026-11-24.md` (generated) and the four run reports it reads (`m1_cleanup_eval_2026-11-24_t07_run1`, `_t07_run2` at 0.7; `_t03_run1`, `_t03_run2` at 0.3). Numbers are quoted from those files.

## Tree state of the runs

- t07_run1 recorded commit 9040ad9, clean.
- t07_run2 and t03_run1 recorded 9040ad9 with "uncommitted changes present"; t03_run2 recorded 715825d with "uncommitted changes present".
- Why: `git_state` then counted untracked files, and each run of the chain left its own report files untracked under `evals/reports/` for the next run; the read_page run2 report was also written there during the chain. No file outside `evals/reports/` was edited during the chain, but the old `git_state` did not record which files it saw, so this rests on the session's record, not on the reports.
- 715825d differs from 9040ad9 only in `evals/reports/m1_cleanup_read_page_check_2026-11-24_run2.md` (git diff in the comparison report), so all four runs ran the same code.
- The runs were not repeated. `git_state` now ignores `evals/reports/` (measuring fix bd25343).
- The four runs are on 9040ad9: items 1-6, before the item 4 follow-up (d3fcdac).

## Results

| | 0.7 run1 | 0.7 run2 | 0.3 run1 | 0.3 run2 |
|---|---|---|---|---|
| turns passing, scorer v2 | 42/42 | 42/42 | 42/42 | 42/42 |
| turns passing, scorer v1 | 42/42 | 41/42 | 41/42 | 42/42 |
| LLM calls per turn, avg | 2.29 | 2.29 | 2.29 | 2.29 |
| turn seconds, avg | 8.3 | 8.1 | 7.8 | 7.8 |

- Verdict flips between the two runs at one temperature: 1 at 0.7 and 1 at 0.3 under v1, both L20 ("Hi Leo, kaise ho?", reply "Hi! Baat karein, kaise ho? 😊", failing only v1's language check); 0 at either temperature under v2.
- Turns whose v2 verdict differs between 0.7 and 0.3: 0 in each of the four pairings.
- Newly failing against the M1.10 baseline (run1, temperature 0.7 from the model's Ollama parameters): v2 on both sides 0 in all four runs; v1 1 in t07_run2 and in t03_run1 (L20, language only).

## Recommendation (the decision is the user's)

Keep 0.7. On these four runs, 0.3 changed no verdict, no pass rate and no LLM-call count; the one turn that flips (L20 under v1) flipped once at each temperature, so 0.3 did not make it steadier. The turn-time difference (8.3 / 8.1 s vs 7.8 / 7.8 s) is small, and two runs per temperature cannot tell it from run-to-run spread. With no measured gain, the plan's rule ("no code change unless the numbers justify it") says leave `llm.primary.temperature` at 0.7.

Limit: two runs per temperature on 42 turns, where the suite passes almost every turn at both settings, cannot show small differences; a harder or larger set would be needed for that.
