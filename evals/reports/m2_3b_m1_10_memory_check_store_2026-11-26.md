# M1.10 eval (memory-check-store) — 2026-11-26 23:24
Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); power: plugged in (battery 100 %)
Commit: f196c5a.
Local model: leo-qwen3. Fallback: openai/gpt-oss-120b. agent.max_steps: 6. All tools are mocks.
Sampling: Leo's requests set temperature 0.7 (config.yaml) and no seed. leo-qwen3 parameters reported by Ollama: temperature 0.7, top_k 20, top_p 0.8; seed: none set. Groq fallback: provider default temperature, no seed.

Suite: evals/scenarios/m1_10_suite.yaml (version 1). Files run: evals/scenarios/m1_7_calendar_turns.yaml (version 1, now 2026-11-16T09:00:00+05:30), evals/scenarios/m1_8_language_turns.yaml (version 1, now 2026-11-16T09:00:00+05:30), evals/scenarios/m1_10_known_failing.yaml (version 1, now 2026-11-16T09:00:00+05:30).
- skipped evals/scenarios/m1_1_schema_check.yaml: single model prompts checked for JSON validity, not chat turns for the graph
- skipped evals/scenarios/m1_6_indian_phrases.yaml: time and number parser phrases, no graph or LLM (checked by evals/m1_6_parser_check.py)
- skipped evals/scenarios/m1_6_heldout_phrases.yaml: time and number parser phrases, no graph or LLM (checked by evals/m1_6_parser_check.py)

## Summary

Turns: 42. pass 28, fail (new) 0, known_failing 0, fixed 14.
Refused calls: 7 (needs approval: 7).

## Metrics

All turns are counted, known failing ones included. A '-' check is not scored for that turn (no tool expectations beyond the plan).

| metric | all | hinglish | en |
|---|---|---|---|
| routing accuracy | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| tool-call accuracy | 41/41 (100.0 %) | 26/26 (100.0 %) | 15/15 (100.0 %) |
| reply checks (all) | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| reply: language | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| reply: clock times match tools | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| reply: no JSON | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| reply: no invented results | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| turn passed (all checks) | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| reply: language (scorer v2) | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| turn passed (all checks, scorer v2) | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| LLM calls per turn | avg 2.3, p50 2.0, p95 4.0, max 5.0 | avg 2.4, p50 2.0, p95 4.0, max 5.0 | avg 2.1, p50 2.0, p95 4.0, max 4.0 |
| refused calls per turn | avg 0.2, p50 0.0, p95 2.0, max 2.0 | avg 0.3, p50 0.0, p95 2.0, max 2.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 |
| fallback (Groq) calls per turn | avg 0.0, p50 0.0, p95 0.0, max 0.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 |
| turn seconds | avg 7.9, p50 6.3, p95 17.3, max 24.2 | avg 8.5, p50 6.4, p95 17.4, max 24.2 | avg 6.8, p50 6.2, p95 14.4, max 14.4 |

## New failures (0)

- none

## New failures with scorer v2 (0)

- none

## Known failing (0)

- none

## Fixed (known failing, now passing) (14)

- m1_7_calendar_turns:t05 [from M1.7]: all checks pass
- m1_7_calendar_turns:t07 [from M1.7]: all checks pass
- m1_7_calendar_turns:t10 [from M1.7, M1.8]: all checks pass
- m1_8_language_turns:L08 [from M1.8]: all checks pass
- m1_8_language_turns:L13 [from M1.8]: all checks pass
- m1_8_language_turns:L17 [from M1.8]: all checks pass
- m1_8_language_turns:I02 [from M1.7, M1.8]: all checks pass
- m1_10_known_failing:K01 [from M1.4]: all checks pass
- m1_10_known_failing:K02 [from M1.7]: all checks pass
- m1_10_known_failing:K03 [from M1.7]: all checks pass
- m1_10_known_failing:K04 [from M1.7, M1.8]: all checks pass
- m1_10_known_failing:K05 [from M1.8]: all checks pass
- m1_10_known_failing:K06 [from M1.8]: all checks pass
- m1_10_known_failing:K07 [from M1.8]: all checks pass

## Refused calls (7)

- m1_7_calendar_turns:t08: cancel_event (needs approval)
- m1_7_calendar_turns:t10: cancel_event (needs approval), cancel_event (needs approval)
- m1_8_language_turns:I02: cancel_event (needs approval), cancel_event (needs approval)
- m1_10_known_failing:K04: cancel_event (needs approval), cancel_event (needs approval)

## Turns

| turn | lang | verdict | verdict v2 | routing | tools | reply | refused | llm_calls | turn_s |
|---|---|---|---|---|---|---|---|---|---|
| m1_7_calendar_turns:t01 | hinglish | pass | pass | ok | ok | ok | 0 | 2 | 6.9 |
| m1_7_calendar_turns:t02 | en | pass | pass | ok | ok | ok | 0 | 2 | 6.6 |
| m1_7_calendar_turns:t03 | hinglish | pass | pass | ok | ok | ok | 0 | 2 | 6.6 |
| m1_7_calendar_turns:t04 | en | pass | pass | ok | ok | ok | 0 | 2 | 6.2 |
| m1_7_calendar_turns:t05 | hinglish | fixed | fixed | ok | ok | ok | 0 | 4 | 12.0 |
| m1_7_calendar_turns:t06 | en | pass | pass | ok | ok | ok | 0 | 4 | 12.7 |
| m1_7_calendar_turns:t07 | hinglish | fixed | fixed | ok | ok | ok | 0 | 1 | 3.3 |
| m1_7_calendar_turns:t08 | hinglish | pass | pass | ok | ok | ok | 1 | 5 | 17.2 |
| m1_7_calendar_turns:t09 | hinglish | pass | pass | ok | ok | ok | 0 | 2 | 6.3 |
| m1_7_calendar_turns:t10 | hinglish | fixed | fixed | ok | ok | ok | 2 | 4 | 17.4 |
| m1_8_language_turns:L01 | hinglish | pass | pass | ok | ok | ok | 0 | 3 | 10.1 |
| m1_8_language_turns:L02 | en | pass | pass | ok | ok | ok | 0 | 3 | 8.9 |
| m1_8_language_turns:L03 | hinglish | pass | pass | ok | ok | ok | 0 | 2 | 6.3 |
| m1_8_language_turns:L04 | en | pass | pass | ok | ok | ok | 0 | 2 | 6.0 |
| m1_8_language_turns:L05 | hinglish | pass | pass | ok | ok | ok | 0 | 2 | 6.1 |
| m1_8_language_turns:L06 | en | pass | pass | ok | ok | ok | 0 | 2 | 6.1 |
| m1_8_language_turns:L07 | hinglish | pass | pass | ok | ok | ok | 0 | 1 | 3.5 |
| m1_8_language_turns:L08 | en | fixed | fixed | ok | ok | ok | 0 | 1 | 3.0 |
| m1_8_language_turns:L09 | hinglish | pass | pass | ok | ok | ok | 0 | 2 | 6.5 |
| m1_8_language_turns:L10 | en | pass | pass | ok | ok | ok | 0 | 2 | 6.2 |
| m1_8_language_turns:L11 | hinglish | pass | pass | ok | ok | ok | 0 | 2 | 6.9 |
| m1_8_language_turns:L12 | en | pass | pass | ok | ok | ok | 0 | 2 | 6.7 |
| m1_8_language_turns:L13 | hinglish | fixed | fixed | ok | ok | ok | 0 | 2 | 6.6 |
| m1_8_language_turns:L14 | en | pass | pass | ok | ok | ok | 0 | 2 | 6.2 |
| m1_8_language_turns:L15 | hinglish | pass | pass | ok | ok | ok | 0 | 1 | 3.3 |
| m1_8_language_turns:L16 | en | pass | pass | ok | ok | ok | 0 | 1 | 3.3 |
| m1_8_language_turns:L17 | hinglish | fixed | fixed | ok | ok | ok | 0 | 1 | 3.7 |
| m1_8_language_turns:L18 | en | pass | pass | ok | ok | ok | 0 | 4 | 14.4 |
| m1_8_language_turns:L19 | hinglish | pass | pass | ok | ok | ok | 0 | 2 | 6.2 |
| m1_8_language_turns:L20 | hinglish | pass | pass | ok | - | ok | 0 | 2 | 5.9 |
| m1_8_language_turns:I01 | hinglish | pass | pass | ok | ok | ok | 0 | 2 | 6.3 |
| m1_8_language_turns:I02 | hinglish | fixed | fixed | ok | ok | ok | 2 | 4 | 17.3 |
| m1_8_language_turns:I03 | hinglish | pass | pass | ok | ok | ok | 0 | 4 | 14.7 |
| m1_8_language_turns:I04 | hinglish | pass | pass | ok | ok | ok | 0 | 2 | 6.4 |
| m1_8_language_turns:I05 | en | pass | pass | ok | ok | ok | 0 | 2 | 6.0 |
| m1_10_known_failing:K01 | en | fixed | fixed | ok | ok | ok | 0 | 2 | 6.1 |
| m1_10_known_failing:K02 | hinglish | fixed | fixed | ok | ok | ok | 0 | 4 | 13.7 |
| m1_10_known_failing:K03 | hinglish | fixed | fixed | ok | ok | ok | 0 | 1 | 3.3 |
| m1_10_known_failing:K04 | hinglish | fixed | fixed | ok | ok | ok | 2 | 4 | 24.2 |
| m1_10_known_failing:K05 | en | fixed | fixed | ok | ok | ok | 0 | 1 | 3.0 |
| m1_10_known_failing:K06 | hinglish | fixed | fixed | ok | ok | ok | 0 | 2 | 6.2 |
| m1_10_known_failing:K07 | hinglish | fixed | fixed | ok | ok | ok | 0 | 1 | 3.6 |

## Comparison

Before: evals/reports/m1.10_eval_2026-11-23_run1.json (Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); commit 9a826ab)
After: evals/reports/m2_3b_m1_10_memory_check_store_2026-11-26.json (Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); power: plugged in (battery 100 %); commit f196c5a)

Code changed between 9a826ab and f196c5a.

The machines differ, so timing rows (turn seconds) are left out; the other metrics do not depend on the machine.

| metric | group | before | after |
|---|---|---|---|
| routing accuracy | all | 40/42 (95.2 %) | 42/42 (100.0 %) |
| routing accuracy | hinglish | 25/27 (92.6 %) | 27/27 (100.0 %) |
| routing accuracy | en | 15/15 (100.0 %) | 15/15 (100.0 %) |
| tool-call accuracy | all | 35/41 (85.4 %) | 41/41 (100.0 %) |
| tool-call accuracy | hinglish | 21/26 (80.8 %) | 26/26 (100.0 %) |
| tool-call accuracy | en | 14/15 (93.3 %) | 15/15 (100.0 %) |
| reply checks (all) | all | 35/42 (83.3 %) | 42/42 (100.0 %) |
| reply checks (all) | hinglish | 20/27 (74.1 %) | 27/27 (100.0 %) |
| reply checks (all) | en | 15/15 (100.0 %) | 15/15 (100.0 %) |
| reply: language | all | 42/42 (100.0 %) | 42/42 (100.0 %) |
| reply: language | hinglish | 27/27 (100.0 %) | 27/27 (100.0 %) |
| reply: language | en | 15/15 (100.0 %) | 15/15 (100.0 %) |
| reply: clock times match tools | all | 37/42 (88.1 %) | 42/42 (100.0 %) |
| reply: clock times match tools | hinglish | 22/27 (81.5 %) | 27/27 (100.0 %) |
| reply: clock times match tools | en | 15/15 (100.0 %) | 15/15 (100.0 %) |
| reply: no JSON | all | 42/42 (100.0 %) | 42/42 (100.0 %) |
| reply: no JSON | hinglish | 27/27 (100.0 %) | 27/27 (100.0 %) |
| reply: no JSON | en | 15/15 (100.0 %) | 15/15 (100.0 %) |
| reply: no invented results | all | 42/42 (100.0 %) | 42/42 (100.0 %) |
| reply: no invented results | hinglish | 27/27 (100.0 %) | 27/27 (100.0 %) |
| reply: no invented results | en | 15/15 (100.0 %) | 15/15 (100.0 %) |
| turn passed (all checks) | all | 34/42 (81.0 %) | 42/42 (100.0 %) |
| turn passed (all checks) | hinglish | 20/27 (74.1 %) | 27/27 (100.0 %) |
| turn passed (all checks) | en | 14/15 (93.3 %) | 15/15 (100.0 %) |
| reply: language (scorer v2) | all | 42/42 (100.0 %) | 42/42 (100.0 %) |
| reply: language (scorer v2) | hinglish | 27/27 (100.0 %) | 27/27 (100.0 %) |
| reply: language (scorer v2) | en | 15/15 (100.0 %) | 15/15 (100.0 %) |
| turn passed (all checks, scorer v2) | all | 34/42 (81.0 %) | 42/42 (100.0 %) |
| turn passed (all checks, scorer v2) | hinglish | 20/27 (74.1 %) | 27/27 (100.0 %) |
| turn passed (all checks, scorer v2) | en | 14/15 (93.3 %) | 15/15 (100.0 %) |
| LLM calls per turn | all | avg 3.1, p50 3.0, p95 7.0, max 7.0 | avg 2.3, p50 2.0, p95 4.0, max 5.0 |
| LLM calls per turn | hinglish | avg 3.3, p50 3.0, p95 7.0, max 7.0 | avg 2.4, p50 2.0, p95 4.0, max 5.0 |
| LLM calls per turn | en | avg 2.8, p50 3.0, p95 4.0, max 4.0 | avg 2.1, p50 2.0, p95 4.0, max 4.0 |
| refused calls per turn | all | avg 0.1, p50 0.0, p95 1.0, max 1.0 | avg 0.2, p50 0.0, p95 2.0, max 2.0 |
| refused calls per turn | hinglish | avg 0.1, p50 0.0, p95 1.0, max 1.0 | avg 0.3, p50 0.0, p95 2.0, max 2.0 |
| refused calls per turn | en | avg 0.1, p50 0.0, p95 1.0, max 1.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 |
| fallback (Groq) calls per turn | all | avg 0.0, p50 0.0, p95 0.0, max 0.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 |
| fallback (Groq) calls per turn | hinglish | avg 0.0, p50 0.0, p95 0.0, max 0.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 |
| fallback (Groq) calls per turn | en | avg 0.0, p50 0.0, p95 0.0, max 0.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 |

Turns whose verdict changed: 8

- m1_7_calendar_turns:t10: known_failing -> fixed
- m1_8_language_turns:L13: known_failing -> fixed
- m1_8_language_turns:L17: known_failing -> fixed
- m1_8_language_turns:I02: known_failing -> fixed
- m1_10_known_failing:K04: known_failing -> fixed
- m1_10_known_failing:K05: known_failing -> fixed
- m1_10_known_failing:K06: known_failing -> fixed
- m1_10_known_failing:K07: known_failing -> fixed

Newly failing turns: 0

- none

Newly failing turns, scorer v2 on both sides: 0

- none

## Details

### m1_7_calendar_turns:t01 (hinglish): pass

**You:** Kal subah 10 baje Rahul ke saath meeting daal do

**Leo:** Ho gaya! 'Meeting with Rahul' Tue 17 Nov, 10:00-11:00 am calendar mein daal diya.

Language: Hindi markers: ['ho', 'gaya', 'mein', 'daal', 'diya']
Language (v2): v2 language hinglish, Hindi markers: ['ho', 'gaya', 'mein', 'daal', 'diya']; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 250 tok 2.7/3.3 s, agent:ollama 399 tok 3.3/3.6 s

Tool calls:
- `create_event({'title': 'Meeting with Rahul', 'start': '2026-11-17T10:00:00+05:30', 'end': '2026-11-17T11:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-17T10:00:00+05:30', 'end': '2026-11-17T11:00:00+05:30', 'title': 'Meeting with Rahul'}`

### m1_7_calendar_turns:t02 (en): pass

**You:** Add a dentist appointment on Thursday at 4:30 pm

**Leo:** Done! Added 'Dentist Appointment' on Thu 19 Nov, 4:30-5:30 pm.

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 247 tok 2.4/3.0 s, agent:ollama 370 tok 3.3/3.6 s

Tool calls:
- `create_event({'title': 'Dentist Appointment', 'start': '2026-11-19T16:30:00+05:30', 'end': '2026-11-19T17:30:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-19T16:30:00+05:30', 'end': '2026-11-19T17:30:00+05:30', 'title': 'Dentist Appointment'}`

### m1_7_calendar_turns:t03 (hinglish): pass

**You:** Thursday dopahar free hoon?

**Leo:** Thu 19 Nov ko aap free ho: 12:00-1:00 pm aur 2:00-4:00 pm.

Language: Hindi markers: ['ko', 'aap', 'ho', 'aur']
Language (v2): v2 language hinglish, Hindi markers: ['ko', 'aap', 'ho', 'aur']; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 242 tok 2.4/2.9 s, agent:ollama 375 tok 3.4/3.7 s

Tool calls:
- `find_free_slots({'start': '2026-11-19T12:00:00+05:30', 'end': '2026-11-19T16:00:00+05:30'})` -> `[{'start': '2026-11-19T12:00:00+05:30', 'end': '2026-11-19T13:00:00+05:30'}, {'start': '2026-11-19T14:00:00+05:30', 'end': '2026-11-19T16:00:00+05:30'}]`

### m1_7_calendar_turns:t04 (en): pass

**You:** Am I free tomorrow evening?

**Leo:** You're free on Tue 17 Nov: 4:00-8:00 pm.

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 240 tok 2.3/2.8 s, agent:ollama 369 tok 3.1/3.3 s

Tool calls:
- `find_free_slots({'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T20:00:00+05:30'})` -> `[{'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T20:00:00+05:30'}]`

### m1_7_calendar_turns:t05 (hinglish): fixed

**You:** 3 baje wali meeting 5 baje kar do

**Leo:** 3 baje ke baad ke meeting ko 5 baje par shift kiya gaya hai.

Language: Hindi markers: ['baje', 'ke', 'ke', 'ko', 'baje', 'kiya', 'gaya', 'hai']
Language (v2): v2 language hinglish, Hindi markers: ['baje', 'ke', 'ke', 'ko', 'baje', 'kiya', 'gaya', 'hai']; verdict with v2: fixed
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 246 tok 2.5/3.0 s, agent:ollama 399 tok 2.2/2.5 s, agent:ollama 501 tok 3.0/3.6 s, responder:ollama 394 tok 2.2/2.8 s

Tool calls:
- `get_events({'start': '2026-11-16T00:00:00+05:30', 'end': '2026-11-17T00:00:00+05:30'})` -> `[{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T15:00:00+05:30', 'end': '2026-11-16T16:00:00+05:30'}]`
- `move_event({'event_id': 'mock-evt-team', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'})` -> `{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}`

### m1_7_calendar_turns:t06 (en): pass

**You:** Move my 3 pm meeting to 5 pm

**Leo:** Done! Your meeting is now at 5:00 pm.

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 244 tok 2.5/2.9 s, agent:ollama 394 tok 3.0/3.2 s, agent:ollama 496 tok 3.0/3.7 s, responder:ollama 372 tok 2.5/2.8 s

Tool calls:
- `get_events({'start': '2026-11-16T00:00:00+05:30', 'end': '2026-11-17T00:00:00+05:30'})` -> `[{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T15:00:00+05:30', 'end': '2026-11-16T16:00:00+05:30'}]`
- `move_event({'event_id': 'mock-evt-team', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'})` -> `{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}`

### m1_7_calendar_turns:t07 (hinglish): fixed

**You:** Saturday ko kya kya hai?

**Leo:** Sat 21 Nov ko aapke calendar mein hai: 'Gym' (8:00-9:00 am) aur 'Call' (10:00-10:30 am).

Language: Hindi markers: ['ko', 'aapke', 'mein', 'hai', 'aur']
Language (v2): v2 language hinglish, Hindi markers: ['ko', 'aapke', 'mein', 'hai', 'aur']; verdict with v2: fixed
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: agent:ollama 352 tok 3.0/3.2 s

Tool calls:
- `get_events({'start': '2026-11-21T00:00:00+05:30', 'end': '2026-11-22T00:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`

### m1_7_calendar_turns:t08 (hinglish): pass

**You:** Saturday ka gym cancel kar do

**Leo:** Gym cancel karne ka request kiya gaya hai, lekin iska approval aapke hissa se hoga. Cancel nahi kiya gaya.

Language: Hindi markers: ['ka', 'kiya', 'gaya', 'hai', 'lekin', 'aapke', 'se', 'hoga', 'nahi', 'kiya', 'gaya']
Language (v2): v2 language hinglish, Hindi markers: ['karne', 'ka', 'kiya', 'gaya', 'hai', 'lekin', 'aapke', 'se', 'hoga', 'nahi', 'kiya', 'gaya']; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 240 tok 2.3/2.8 s, agent:ollama 360 tok 2.8/3.1 s, agent:ollama 538 tok 3.5/3.9 s, agent:ollama 584 tok 2.6/3.1 s, responder:ollama 475 tok 3.5/4.4 s

Tool calls:
- `get_events({'start': '2026-11-21T00:00:00+05:30', 'end': '2026-11-22T00:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`
- `cancel_event({'event_id': 'mock-evt-gym'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`

### m1_7_calendar_turns:t09 (hinglish): pass

**You:** Kal Rahul ke saath meeting

**Leo:** Kal kya hai? Aane wala kal ya beeta hua kal?

Language: Hindi markers: ['kal', 'kya', 'hai', 'wala', 'kal', 'hua', 'kal']
Language (v2): v2 language hinglish, Hindi markers: ['kal', 'kya', 'hai', 'wala', 'kal', 'hua', 'kal']; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'ask'}
LLM calls: supervisor:ollama 240 tok 2.4/2.9 s, responder:ollama 374 tok 3.0/3.4 s

Tool calls:
- none

### m1_7_calendar_turns:t10 (hinglish): fixed

**You:** Agar Saturday ko baarish nahi hogi to subah 7 baje Lonavala trip plan kar do, aur Saturday subah clear kar do.

**Leo:** Sat 21 Nov ka forecast check kiya: 5% baarish ka chance hai. 'Trip to Lonavala Saturday Morning 7 AM' Sat 21 Nov, 7:00-8:00 am calendar mein daal diya. 'Gym' (Sat 21 Nov, 8:00-9:00 am) aur 'Call' (Sat 21 Nov, 10:00-10:30 am) cancel karne ke liye pehle aapki approval chahiye; abhi kuch cancel nahi hua.

Language: Hindi markers: ['ka', 'kiya', 'ka', 'hai', 'mein', 'daal', 'diya', 'aur', 'ke', 'liye', 'aapki', 'chahiye', 'abhi', 'kuch', 'nahi', 'hua']
Language (v2): v2 language hinglish, Hindi markers: ['ka', 'kiya', 'ka', 'hai', 'mein', 'daal', 'diya', 'aur', 'karne', 'ke', 'liye', 'aapki', 'chahiye', 'abhi', 'kuch', 'nahi', 'hua']; verdict with v2: fixed
Plan: [['research', 'calendar']]; stops: {'research': 'done', 'calendar': 'done'}
LLM calls: supervisor:ollama 268 tok 2.6/3.6 s, agent:ollama 302 tok 3.1/3.3 s, agent:ollama 404 tok 3.0/6.2 s, agent:ollama 452 tok 3.6/4.2 s

Tool calls:
- `get_weather({'place': 'Lonavala'})` -> `{'place': 'Lonavala, Maharashtra, India', 'days': [{'date': '2026-11-21', 'day': 'Saturday', 'rain_chance_pct': 5, 'rain_mm': 0.0}], 'source': 'Open-Meteo', 'source_url': 'https://open-meteo.com'}`
- `get_events({'start': '2026-11-21T06:00:00+05:30', 'end': '2026-11-21T12:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`
- `cancel_event({'event_id': 'mock-evt-gym'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`
- `cancel_event({'event_id': 'mock-evt-call'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`
- `create_event({'title': 'Trip to Lonavala Saturday Morning 7 AM', 'start': '2026-11-21T07:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-21T07:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30', 'title': 'Trip to Lonavala Saturday Morning 7 AM'}`

### m1_8_language_turns:L01 (hinglish): pass

**You:** Kal Pune mein baarish hogi?

**Leo:** No, kal Pune mein baarish nahi hogi. 70% chance of rain (Open-Meteo).

Language: Hindi markers: ['kal', 'mein', 'nahi', 'hogi']
Language (v2): v2 language hinglish, Hindi markers: ['kal', 'mein', 'nahi', 'hogi']; verdict with v2: pass
Plan: [['research']]; stops: {'research': 'done'}
LLM calls: supervisor:ollama 243 tok 2.5/2.9 s, agent:ollama 256 tok 2.7/3.0 s, responder:ollama 430 tok 3.6/4.2 s

Tool calls:
- `get_weather({'place': 'Pune'})` -> `{'place': 'Pune, Maharashtra, India', 'days': [{'date': '2026-11-16', 'day': 'today', 'rain_chance_pct': 10, 'rain_mm': 0.0}, {'date': '2026-11-17', 'day': 'tomorrow', 'rain_chance_pct': 70, 'rain_mm': 6.2}, {'date': '2026-11-21', 'day': 'Saturday', 'rain_chance_pct': 5, 'rain_mm': 0.0}], 'source': 'Open-Meteo', 'source_url': 'https://open-meteo.com'}`

### m1_8_language_turns:L02 (en): pass

**You:** Will it rain in Pune tomorrow?

**Leo:** Yes, it is likely to rain in Pune tomorrow, with a 70% chance (Open-Meteo).

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: pass
Plan: [['research']]; stops: {'research': 'done'}
LLM calls: supervisor:ollama 241 tok 2.4/2.8 s, agent:ollama 254 tok 2.7/2.9 s, responder:ollama 408 tok 2.5/3.0 s

Tool calls:
- `get_weather({'place': 'Pune'})` -> `{'place': 'Pune, Maharashtra, India', 'days': [{'date': '2026-11-16', 'day': 'today', 'rain_chance_pct': 10, 'rain_mm': 0.0}, {'date': '2026-11-17', 'day': 'tomorrow', 'rain_chance_pct': 70, 'rain_mm': 6.2}, {'date': '2026-11-21', 'day': 'Saturday', 'rain_chance_pct': 5, 'rain_mm': 0.0}], 'source': 'Open-Meteo', 'source_url': 'https://open-meteo.com'}`

### m1_8_language_turns:L03 (hinglish): pass

**You:** Doodh ko meri tasks list mein daal do

**Leo:** 'Doodh' aapki tasks list mein daal diya.

Language: Hindi markers: ['aapki', 'mein', 'daal', 'diya']
Language (v2): v2 language hinglish, Hindi markers: ['aapki', 'mein', 'daal', 'diya']; verdict with v2: pass
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 246 tok 2.5/3.0 s, agent:ollama 343 tok 3.0/3.2 s

Tool calls:
- `add_task({'title': 'Doodh'})` -> `{'id': 3, 'title': 'Doodh', 'done': False}`

### m1_8_language_turns:L04 (en): pass

**You:** Add bread to my tasks

**Leo:** Added 'bread' to your tasks.

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: pass
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 239 tok 2.4/2.9 s, agent:ollama 334 tok 2.9/3.1 s

Tool calls:
- `add_task({'title': 'bread'})` -> `{'id': 3, 'title': 'bread', 'done': False}`

### m1_8_language_turns:L05 (hinglish): pass

**You:** Milk wala task complete kar do

**Leo:** 'Buy milk' task complete mark kar diya.

Language: Hindi markers: ['kar', 'diya']
Language (v2): v2 language hinglish, Hindi markers: ['kar', 'diya']; verdict with v2: pass
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 242 tok 2.4/2.9 s, agent:ollama 338 tok 2.9/3.2 s

Tool calls:
- `complete_task({'title': 'milk'})` -> `{'id': 1, 'title': 'Buy milk', 'done': True}`

### m1_8_language_turns:L06 (en): pass

**You:** Mark the electricity bill task as done

**Leo:** Marked 'Pay electricity bill' as done.

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: pass
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 241 tok 2.4/3.0 s, agent:ollama 339 tok 2.8/3.0 s

Tool calls:
- `complete_task({'title': 'electricity bill'})` -> `{'id': 2, 'title': 'Pay electricity bill', 'done': True}`

### m1_8_language_turns:L07 (hinglish): pass

**You:** 2450 ka 18 percent kitna hai?

**Leo:** 18% of 2450 ka jawab 441 hai.

Language: Hindi markers: ['ka', 'hai']
Language (v2): v2 language hinglish, Hindi markers: ['ka', 'hai']; verdict with v2: pass
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 247 tok 2.5/3.0 s

Tool calls:
- `calculate({'expression': '18% of 2450'})` -> `{'expression': '18% of 2450', 'computed': '(18/100)*2450', 'result': '441'}`

### m1_8_language_turns:L08 (en): fixed

**You:** What is 15% of 3200?

**Leo:** 15% of 3200 = 480.

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: fixed
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 247 tok 2.5/3.0 s

Tool calls:
- `calculate({'expression': '15% of 3200'})` -> `{'expression': '15% of 3200', 'computed': '(15/100)*3200', 'result': '480'}`

### m1_8_language_turns:L09 (hinglish): pass

**You:** Chai ke liye 10 minute ka timer laga do

**Leo:** 'chai' ka timer 10 minute ke liye laga diya.

Language: Hindi markers: ['ka', 'ke', 'liye', 'diya']
Language (v2): v2 language hinglish, Hindi markers: ['ka', 'ke', 'liye', 'diya']; verdict with v2: pass
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 248 tok 2.5/3.0 s, agent:ollama 344 tok 2.9/3.3 s

Tool calls:
- `start_timer({'minutes': 10.0, 'label': 'chai'})` -> `{'label': 'chai', 'minutes': 10.0, 'ends_at': '2026-11-14T08:10:00+05:30'}`

### m1_8_language_turns:L10 (en): pass

**You:** Set a 5 minute timer for the eggs

**Leo:** Timer 'eggs' set for 5 minutes.

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: pass
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 243 tok 2.3/2.8 s, agent:ollama 339 tok 2.9/3.3 s

Tool calls:
- `start_timer({'minutes': 5.0, 'label': 'eggs'})` -> `{'label': 'eggs', 'minutes': 5.0, 'ends_at': '2026-11-14T08:05:00+05:30'}`

### m1_8_language_turns:L11 (hinglish): pass

**You:** Kal subah 10 baje Rahul ke saath meeting daal do

**Leo:** Ho gaya! 'Meeting with Rahul' Tue 17 Nov, 10:00-11:00 am calendar mein daal diya.

Language: Hindi markers: ['ho', 'gaya', 'mein', 'daal', 'diya']
Language (v2): v2 language hinglish, Hindi markers: ['ho', 'gaya', 'mein', 'daal', 'diya']; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 250 tok 2.4/3.0 s, agent:ollama 399 tok 3.5/3.8 s

Tool calls:
- `create_event({'title': 'Meeting with Rahul', 'start': '2026-11-17T10:00:00+05:30', 'end': '2026-11-17T11:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-17T10:00:00+05:30', 'end': '2026-11-17T11:00:00+05:30', 'title': 'Meeting with Rahul'}`

### m1_8_language_turns:L12 (en): pass

**You:** Add a dentist appointment on Thursday at 4:30 pm

**Leo:** Done! Added 'Dentist Appointment' on Thu 19 Nov, 4:30-5:30 pm.

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 247 tok 2.5/3.1 s, agent:ollama 370 tok 3.3/3.6 s

Tool calls:
- `create_event({'title': 'Dentist Appointment', 'start': '2026-11-19T16:30:00+05:30', 'end': '2026-11-19T17:30:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-19T16:30:00+05:30', 'end': '2026-11-19T17:30:00+05:30', 'title': 'Dentist Appointment'}`

### m1_8_language_turns:L13 (hinglish): fixed

**You:** Thursday dopahar free hoon?

**Leo:** Thu 19 Nov ko aap free ho: 12:00-1:00 pm aur 2:00-4:00 pm.

Language: Hindi markers: ['ko', 'aap', 'ho', 'aur']
Language (v2): v2 language hinglish, Hindi markers: ['ko', 'aap', 'ho', 'aur']; verdict with v2: fixed
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 242 tok 2.4/2.9 s, agent:ollama 375 tok 3.4/3.7 s

Tool calls:
- `find_free_slots({'start': '2026-11-19T12:00:00+05:30', 'end': '2026-11-19T16:00:00+05:30'})` -> `[{'start': '2026-11-19T12:00:00+05:30', 'end': '2026-11-19T13:00:00+05:30'}, {'start': '2026-11-19T14:00:00+05:30', 'end': '2026-11-19T16:00:00+05:30'}]`

### m1_8_language_turns:L14 (en): pass

**You:** Am I free tomorrow evening?

**Leo:** You're free on Tue 17 Nov: 4:00-8:00 pm.

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 240 tok 2.4/2.8 s, agent:ollama 369 tok 3.1/3.4 s

Tool calls:
- `find_free_slots({'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T20:00:00+05:30'})` -> `[{'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T20:00:00+05:30'}]`

### m1_8_language_turns:L15 (hinglish): pass

**You:** Saturday ko kya kya hai?

**Leo:** Sat 21 Nov ko aapke calendar mein hai: 'Gym' (8:00-9:00 am) aur 'Call' (10:00-10:30 am).

Language: Hindi markers: ['ko', 'aapke', 'mein', 'hai', 'aur']
Language (v2): v2 language hinglish, Hindi markers: ['ko', 'aapke', 'mein', 'hai', 'aur']; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: agent:ollama 352 tok 3.0/3.2 s

Tool calls:
- `get_events({'start': '2026-11-21T00:00:00+05:30', 'end': '2026-11-22T00:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`

### m1_8_language_turns:L16 (en): pass

**You:** What's on my calendar on Thursday?

**Leo:** On Thu 19 Nov you have: 'Lunch with Neha' (1:00-2:00 pm).

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: agent:ollama 352 tok 3.0/3.2 s

Tool calls:
- `get_events({'start': '2026-11-19T00:00:00+05:30', 'end': '2026-11-20T00:00:00+05:30'})` -> `[{'id': 'mock-evt-lunch', 'title': 'Lunch with Neha', 'start': '2026-11-19T13:00:00+05:30', 'end': '2026-11-19T14:00:00+05:30'}]`

### m1_8_language_turns:L17 (hinglish): fixed

**You:** Aaj shaam 5 baje kya hai?

**Leo:** Mon 16 Nov ko aapke calendar mein hai: 'Review call' (5:00-6:00 pm).

Language: Hindi markers: ['ko', 'aapke', 'mein', 'hai']
Language (v2): v2 language hinglish, Hindi markers: ['ko', 'aapke', 'mein', 'hai']; verdict with v2: fixed
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: agent:ollama 391 tok 3.4/3.7 s

Tool calls:
- `get_events({'start': '2026-11-16T16:00:00+05:30', 'end': '2026-11-16T20:00:00+05:30'})` -> `[{'id': 'mock-evt-review', 'title': 'Review call', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}]`

### m1_8_language_turns:L18 (en): pass

**You:** Move my 5 pm call to 6 pm

**Leo:** Your 5 pm review call has been moved to 6 pm. Calendar updated.

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 244 tok 2.4/2.9 s, agent:ollama 394 tok 3.5/3.7 s, agent:ollama 572 tok 3.6/4.2 s, responder:ollama 394 tok 3.0/3.5 s

Tool calls:
- `get_events({'start': '2026-11-16T00:00:00+05:30', 'end': '2026-11-17T00:00:00+05:30'})` -> `[{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T15:00:00+05:30', 'end': '2026-11-16T16:00:00+05:30'}, {'id': 'mock-evt-review', 'title': 'Review call', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}]`
- `move_event({'event_id': 'mock-evt-review', 'start': '2026-11-16T18:00:00+05:30', 'end': '2026-11-16T19:00:00+05:30'})` -> `{'id': 'mock-evt-review', 'title': 'Review call', 'start': '2026-11-16T18:00:00+05:30', 'end': '2026-11-16T19:00:00+05:30'}`

### m1_8_language_turns:L19 (hinglish): pass

**You:** Ek note likh lo: gas cylinder book karna hai

**Leo:** Note save kar diya.

Language: Hindi markers: ['kar', 'diya']
Language (v2): v2 language hinglish, Hindi markers: ['kar', 'diya']; verdict with v2: pass
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 246 tok 2.5/2.9 s, agent:ollama 341 tok 2.9/3.3 s

Tool calls:
- `add_note({'text': 'gas cylinder book karna hai'})` -> `{'id': 2, 'text': 'gas cylinder book karna hai'}`

### m1_8_language_turns:L20 (hinglish): pass

**You:** Hi Leo, kaise ho?

**Leo:** Hey! Baat karne ke liye bahut accha, thank you! 😊

Language: Hindi markers: ['ke', 'liye', 'accha']
Language (v2): v2 language hinglish, Hindi markers: ['baat', 'karne', 'ke', 'liye', 'accha']; verdict with v2: pass
Plan: [[]]; stops: no agent run
LLM calls: supervisor:ollama 241 tok 2.3/2.7 s, responder:ollama 325 tok 2.7/3.2 s

Tool calls:
- none

### m1_8_language_turns:I01 (hinglish): pass

**You:** Saturday ko free time kab hai?

**Leo:** Sat 21 Nov ko aap free ho: 6:00-8:00 am, 9:00-10:00 am aur 10:30 am-11:00 pm.

Language: Hindi markers: ['ko', 'aap', 'ho', 'aur']
Language (v2): v2 language hinglish, Hindi markers: ['ko', 'aap', 'ho', 'aur']; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 241 tok 2.4/3.0 s, agent:ollama 349 tok 3.0/3.3 s

Tool calls:
- `find_free_slots({'start': '2026-11-21T06:00:00+05:30', 'end': '2026-11-21T23:00:00+05:30'})` -> `[{'start': '2026-11-21T06:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30'}, {'start': '2026-11-21T09:00:00+05:30', 'end': '2026-11-21T10:00:00+05:30'}, {'start': '2026-11-21T10:30:00+05:30', 'end': '2026-11-21T23:00:00+05:30'}]`

### m1_8_language_turns:I02 (hinglish): fixed

**You:** Agar Saturday ko baarish nahi hogi to subah 7 baje Lonavala trip plan kar do, aur Saturday subah clear kar do.

**Leo:** Sat 21 Nov ka forecast check kiya: 5% baarish ka chance hai. 'Check weather for Lonavala on Saturday' Sat 21 Nov, 7:00-8:00 am calendar mein daal diya. 'Gym' (Sat 21 Nov, 8:00-9:00 am) aur 'Call' (Sat 21 Nov, 10:00-10:30 am) cancel karne ke liye pehle aapki approval chahiye; abhi kuch cancel nahi hua.

Language: Hindi markers: ['ka', 'kiya', 'ka', 'hai', 'mein', 'daal', 'diya', 'aur', 'ke', 'liye', 'aapki', 'chahiye', 'abhi', 'kuch', 'nahi', 'hua']
Language (v2): v2 language hinglish, Hindi markers: ['ka', 'kiya', 'ka', 'hai', 'mein', 'daal', 'diya', 'aur', 'karne', 'ke', 'liye', 'aapki', 'chahiye', 'abhi', 'kuch', 'nahi', 'hua']; verdict with v2: fixed
Plan: [['research', 'calendar']]; stops: {'research': 'done', 'calendar': 'done'}
LLM calls: supervisor:ollama 268 tok 2.6/3.7 s, agent:ollama 305 tok 3.0/3.3 s, agent:ollama 486 tok 3.6/6.0 s, agent:ollama 509 tok 3.9/4.4 s

Tool calls:
- `get_weather({'place': 'Lonavala'})` -> `{'place': 'Lonavala, Maharashtra, India', 'days': [{'date': '2026-11-16', 'day': 'today', 'rain_chance_pct': 10, 'rain_mm': 0.0}, {'date': '2026-11-17', 'day': 'tomorrow', 'rain_chance_pct': 70, 'rain_mm': 6.2}, {'date': '2026-11-21', 'day': 'Saturday', 'rain_chance_pct': 5, 'rain_mm': 0.0}], 'source': 'Open-Meteo', 'source_url': 'https://open-meteo.com'}`
- `get_events({'start': '2026-11-21T06:00:00+05:30', 'end': '2026-11-21T12:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`
- `cancel_event({'event_id': 'mock-evt-gym'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`
- `cancel_event({'event_id': 'mock-evt-call'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`
- `create_event({'title': 'Check weather for Lonavala on Saturday', 'start': '2026-11-21T07:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-21T07:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30', 'title': 'Check weather for Lonavala on Saturday'}`

### m1_8_language_turns:I03 (hinglish): pass

**You:** 3 baje wali meeting 4 baje kar do

**Leo:** 3 baje wali meeting 4 baje kar di gayi. Calendar mein update kiya gaya.

Language: Hindi markers: ['baje', 'wali', 'baje', 'kar', 'di', 'gayi', 'mein', 'kiya', 'gaya']
Language (v2): v2 language hinglish, Hindi markers: ['baje', 'wali', 'baje', 'kar', 'di', 'gayi', 'mein', 'kiya', 'gaya']; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 246 tok 2.5/3.1 s, agent:ollama 399 tok 3.3/3.5 s, agent:ollama 577 tok 3.6/4.2 s, responder:ollama 416 tok 3.3/3.9 s

Tool calls:
- `get_events({'start': '2026-11-16T00:00:00+05:30', 'end': '2026-11-17T00:00:00+05:30'})` -> `[{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T15:00:00+05:30', 'end': '2026-11-16T16:00:00+05:30'}, {'id': 'mock-evt-review', 'title': 'Review call', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}]`
- `move_event({'event_id': 'mock-evt-team', 'start': '2026-11-16T16:00:00+05:30', 'end': '2026-11-16T17:00:00+05:30'})` -> `{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T16:00:00+05:30', 'end': '2026-11-16T17:00:00+05:30'}`

### m1_8_language_turns:I04 (hinglish): pass

**You:** Kal 4 baje dentist appointment daal do

**Leo:** Ho gaya! 'Dentist Appointment' Tue 17 Nov, 4:00-5:00 pm calendar mein daal diya. 4:00 pm hi chahiye tha na?

Language: Hindi markers: ['ho', 'gaya', 'mein', 'daal', 'diya', 'chahiye']
Language (v2): v2 language hinglish, Hindi markers: ['ho', 'gaya', 'mein', 'daal', 'diya', 'chahiye', 'tha']; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 244 tok 2.4/2.9 s, agent:ollama 363 tok 3.2/3.5 s

Tool calls:
- `create_event({'title': 'Dentist Appointment', 'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T17:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T17:00:00+05:30', 'title': 'Dentist Appointment'}`

### m1_8_language_turns:I05 (en): pass

**You:** Add a haircut tomorrow at 4

**Leo:** Done! Added 'Haircut' on Tue 17 Nov, 4:00-5:00 pm. Did you mean 4:00 pm?

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: pass
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 241 tok 2.3/2.8 s, agent:ollama 359 tok 2.9/3.2 s

Tool calls:
- `create_event({'title': 'Haircut', 'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T17:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T17:00:00+05:30', 'title': 'Haircut'}`

### m1_10_known_failing:K01 (en): fixed

**You:** complete my milk task

**Leo:** Marked 'Buy milk' as done.

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: fixed
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 238 tok 2.4/2.9 s, agent:ollama 334 tok 2.9/3.1 s

Tool calls:
- `complete_task({'title': 'milk'})` -> `{'id': 1, 'title': 'Buy milk', 'done': True}`

### m1_10_known_failing:K02 (hinglish): fixed

**You:** 3 baje wali meeting 5 baje kar do

**Leo:** 3 baje ke meeting ko 5 baje par badal diya gaya.

Language: Hindi markers: ['baje', 'ke', 'ko', 'baje', 'diya', 'gaya']
Language (v2): v2 language hinglish, Hindi markers: ['baje', 'ke', 'ko', 'baje', 'diya', 'gaya']; verdict with v2: fixed
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 246 tok 2.4/2.9 s, agent:ollama 396 tok 3.3/3.6 s, agent:ollama 498 tok 3.0/3.6 s, responder:ollama 394 tok 3.1/3.5 s

Tool calls:
- `get_events({'start': '2026-11-16T00:00:00+05:30', 'end': '2026-11-17T00:00:00+05:30'})` -> `[{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T15:00:00+05:30', 'end': '2026-11-16T16:00:00+05:30'}]`
- `move_event({'event_id': 'mock-evt-team', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'})` -> `{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}`

### m1_10_known_failing:K03 (hinglish): fixed

**You:** Saturday ko kya kya hai?

**Leo:** Sat 21 Nov ko aapke calendar mein hai: 'Gym' (8:00-9:00 am) aur 'Call' (10:00-10:30 am).

Language: Hindi markers: ['ko', 'aapke', 'mein', 'hai', 'aur']
Language (v2): v2 language hinglish, Hindi markers: ['ko', 'aapke', 'mein', 'hai', 'aur']; verdict with v2: fixed
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: agent:ollama 352 tok 3.0/3.3 s

Tool calls:
- `get_events({'start': '2026-11-21T00:00:00+05:30', 'end': '2026-11-22T00:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`

### m1_10_known_failing:K04 (hinglish): fixed

**You:** Agar Saturday ko baarish nahi hogi to subah 7 baje Lonavala trip plan kar do, aur Saturday subah clear kar do.

**Leo:** Sat 21 Nov ka forecast check kiya: 5% baarish ka chance hai. 'Lonavala Trip - Saturday 7 AM' Sat 21 Nov, 7:00-8:00 am calendar mein daal diya. 'Gym' (Sat 21 Nov, 8:00-9:00 am) aur 'Call' (Sat 21 Nov, 10:00-10:30 am) cancel karne ke liye pehle aapki approval chahiye; abhi kuch cancel nahi hua.

Language: Hindi markers: ['ka', 'kiya', 'ka', 'hai', 'mein', 'daal', 'diya', 'aur', 'ke', 'liye', 'aapki', 'chahiye', 'abhi', 'kuch', 'nahi', 'hua']
Language (v2): v2 language hinglish, Hindi markers: ['ka', 'kiya', 'ka', 'hai', 'mein', 'daal', 'diya', 'aur', 'karne', 'ke', 'liye', 'aapki', 'chahiye', 'abhi', 'kuch', 'nahi', 'hua']; verdict with v2: fixed
Plan: [['research', 'calendar']]; stops: {'research': 'done', 'calendar': 'done'}
LLM calls: supervisor:ollama 268 tok 2.6/3.6 s, agent:ollama 300 tok 3.1/3.4 s, agent:ollama 481 tok 3.5/12.8 s, agent:ollama 504 tok 4.0/4.5 s

Tool calls:
- `get_weather({'place': 'Lonavala'})` -> `{'place': 'Lonavala, Maharashtra, India', 'days': [{'date': '2026-11-16', 'day': 'today', 'rain_chance_pct': 10, 'rain_mm': 0.0}, {'date': '2026-11-17', 'day': 'tomorrow', 'rain_chance_pct': 70, 'rain_mm': 6.2}, {'date': '2026-11-21', 'day': 'Saturday', 'rain_chance_pct': 5, 'rain_mm': 0.0}], 'source': 'Open-Meteo', 'source_url': 'https://open-meteo.com'}`
- `get_events({'start': '2026-11-21T06:00:00+05:30', 'end': '2026-11-21T12:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`
- `cancel_event({'event_id': 'mock-evt-gym'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`
- `cancel_event({'event_id': 'mock-evt-call'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`
- `create_event({'title': 'Lonavala Trip - Saturday 7 AM', 'start': '2026-11-21T07:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-21T07:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30', 'title': 'Lonavala Trip - Saturday 7 AM'}`

### m1_10_known_failing:K05 (en): fixed

**You:** What is 15% of 3200?

**Leo:** 15% of 3200 = 480.

Language: Hindi markers outside tool data: []
Language (v2): v2 language en, Hindi markers: []; verdict with v2: fixed
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 247 tok 2.4/3.0 s

Tool calls:
- `calculate({'expression': '15% of 3200'})` -> `{'expression': '15% of 3200', 'computed': '(15/100)*3200', 'result': '480'}`

### m1_10_known_failing:K06 (hinglish): fixed

**You:** Thursday dopahar free hoon?

**Leo:** Thu 19 Nov ko aap free ho: 12:00-1:00 pm aur 2:00-4:00 pm.

Language: Hindi markers: ['ko', 'aap', 'ho', 'aur']
Language (v2): v2 language hinglish, Hindi markers: ['ko', 'aap', 'ho', 'aur']; verdict with v2: fixed
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 242 tok 2.3/2.9 s, agent:ollama 375 tok 3.1/3.3 s

Tool calls:
- `find_free_slots({'start': '2026-11-19T12:00:00+05:30', 'end': '2026-11-19T16:00:00+05:30'})` -> `[{'start': '2026-11-19T12:00:00+05:30', 'end': '2026-11-19T13:00:00+05:30'}, {'start': '2026-11-19T14:00:00+05:30', 'end': '2026-11-19T16:00:00+05:30'}]`

### m1_10_known_failing:K07 (hinglish): fixed

**You:** Aaj shaam 5 baje kya hai?

**Leo:** Mon 16 Nov ko aapke calendar mein hai: 'Review call' (5:00-6:00 pm).

Language: Hindi markers: ['ko', 'aapke', 'mein', 'hai']
Language (v2): v2 language hinglish, Hindi markers: ['ko', 'aapke', 'mein', 'hai']; verdict with v2: fixed
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: agent:ollama 391 tok 3.4/3.6 s

Tool calls:
- `get_events({'start': '2026-11-16T16:00:00+05:30', 'end': '2026-11-16T20:00:00+05:30'})` -> `[{'id': 'mock-evt-review', 'title': 'Review call', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}]`

