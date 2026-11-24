# M1 cleanup item 2: Hinglish gap — 2026-11-24
Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)

Written by hand from these reports; every number below is quoted from them:
- `evals/reports/m1_cleanup_eval_2026-11-24_gap.md` (this item's run, commit 7b711b3, temperature 0.7, 42 turns, with the comparison against M1.10 run1);
- `evals/reports/m1_cleanup_scorer_check_2026-11-24.md` (scorer v1 and v2 on 48 labelled replies).

Measuring only: no Leo code was changed for this item.

## Pass rates (turns passing all checks)

| run | scorer | all | Hinglish | English |
|---|---|---|---|---|
| M1.10 run1 (baseline, rescored from its stored replies) | v1 | 34/42 (81.0 %) | 20/27 (74.1 %) | 14/15 (93.3 %) |
| M1.10 run1 (baseline, rescored from its stored replies) | v2 | 34/42 (81.0 %) | 20/27 (74.1 %) | 14/15 (93.3 %) |
| M1 cleanup gap run | v1 | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| M1 cleanup gap run | v2 | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |

Language check alone in the gap run: 42/42 under v1 and under v2. Newly failing against M1.10 run1: 0 under v1, 0 with v2 on both sides. Fallback (Groq) calls: 0.

## Hinglish turns still failing under v2

None in the gap run.

In the baseline, the 7 Hinglish turns that failed (t10, L13, L17, I02, K04, K06, K07) failed the same checks under both scorers: tool calls, clock times or events not named, and routing for L17 and K07, not the language. All 7 pass in the gap run, after the M1 exit check's code changes. So, on these numbers, the Hinglish/English gap in the baseline came from calendar and routing behaviour that hit Hinglish turns more often, not from the language scorer.

L20 "Hi Leo, kaise ho?" passed in the gap run under both scorers, with the reply "Hi! Baat karo, kaise ho? 😊". The run6 reply that v1 failed ("Hi! Baat karein, kaise ho? 😊") is case r01 of the scorer check set: v1 FAIL, v2 hinglish.

## Limits of this measurement

- One run only. M1 exit run5 and run6 show that a verdict can flip between runs with no code change (L20), so 27/27 in one run does not show the run-to-run rate. The item 7 runs (two at 0.7, two at 0.3 on one commit) add four more runs.
- v2 marker list: the rule's shape was fixed in the plan before the check set, but the extra marker words were chosen after the check set was written, by the same author. The check set result (v2 47/48) is therefore not an independent measure; a fresh held-out set written by someone else would be.

## Proposed fixes (not made)

- None needed for a Hinglish turn on this run.
- If later runs show Hinglish failures again, look first at the turn's tool and reply checks, as above, before the language scorer.
- Scorer: r48 (an English reply quoting the user's "kal wali PDF") is read as Hinglish by v2 and fails v1. A fix would count words quoted from the user's message like tool data; it would be a scorer v3 with a fresh check set.
