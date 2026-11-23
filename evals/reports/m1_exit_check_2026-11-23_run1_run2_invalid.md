# M1 exit check: run1 and run2 are invalid for the exit rule

Reports: `evals/reports/m1_exit_eval_2026-11-23_run1.md` / `.json` and
`evals/reports/m1_exit_eval_2026-11-23_run2.md` / `.json` (laptop, commit e75f4fa).
They stay in the repository as they ran. The exit rule
(`evals/scenarios/m1_exit_rule.yaml`) is NOT applied to them.

Why: a bug in the measuring tool, not in Leo. The runner took each turn's plan
only from the supervisor's LLM reply (`chosen()` in `evals/m1_5_check_helpers.py`,
used by `evals/m1_8_check.run_one`). Since the K07 fix (commit d13ecfa), calendar
queries are planned by code with no supervisor LLM call, so the runner recorded
plan `[]` and scored routing as failed for those turns, although the calendar
agent ran and every tool and reply check passed. Affected in both runs:
m1_7 t07, m1_8 L15, L16, L17, m1_10 K03, K07. L15 and L16 therefore show as
newly failing against the M1.10 baseline.

Fix: commit cb4e490 (runner only; scoring rules and scenario files unchanged):
the plan is now the agents that actually ran. The exit rule is applied to two
fresh runs on the fixed runner, written as run3 and run4.

Also seen, not caused by the runner bug: in run1, m1_8 L20 ("Hi Leo, kaise ho?")
failed the language check. The reply was "Hi! Baat karein, kaise ho? 😊" (one
Hindi marker, 'ho'). No agent ran (plan `[]`, correct); the reply came from the
LLM responder. L20 passed in run2. Not fixed (as agreed).
