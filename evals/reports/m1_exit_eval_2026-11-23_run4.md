# M1.10 eval (M1 exit run4) — 2026-11-24 00:02
Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)
Commit: 575e084.
Local model: leo-qwen3. Fallback: openai/gpt-oss-120b. agent.max_steps: 6. All tools are mocks.
Sampling: Leo's requests set temperature 0.7 (config.yaml) and no seed. leo-qwen3 parameters reported by Ollama: temperature 0.7, top_k 20, top_p 0.8; seed: none set. Groq fallback: provider default temperature, no seed.

Suite: evals/scenarios/m1_10_suite.yaml (version 1). Files run: evals/scenarios/m1_7_calendar_turns.yaml (version 1, now 2026-11-16T09:00:00+05:30), evals/scenarios/m1_8_language_turns.yaml (version 1, now 2026-11-16T09:00:00+05:30), evals/scenarios/m1_10_known_failing.yaml (version 1, now 2026-11-16T09:00:00+05:30).
- skipped evals/scenarios/m1_1_schema_check.yaml: single model prompts checked for JSON validity, not chat turns for the graph
- skipped evals/scenarios/m1_6_indian_phrases.yaml: time and number parser phrases, no graph or LLM (checked by evals/m1_6_parser_check.py)
- skipped evals/scenarios/m1_6_heldout_phrases.yaml: time and number parser phrases, no graph or LLM (checked by evals/m1_6_parser_check.py)

## Summary

Turns: 42. pass 27, fail (new) 1, known_failing 1, fixed 13.
Refused calls: 7 (needs approval: 7).

## Metrics

All turns are counted, known failing ones included. A '-' check is not scored for that turn (no tool expectations beyond the plan).

| metric | all | hinglish | en |
|---|---|---|---|
| routing accuracy | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| tool-call accuracy | 41/41 (100.0 %) | 26/26 (100.0 %) | 15/15 (100.0 %) |
| reply checks (all) | 40/42 (95.2 %) | 25/27 (92.6 %) | 15/15 (100.0 %) |
| reply: language | 41/42 (97.6 %) | 26/27 (96.3 %) | 15/15 (100.0 %) |
| reply: clock times match tools | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| reply: no JSON | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| reply: no invented results | 42/42 (100.0 %) | 27/27 (100.0 %) | 15/15 (100.0 %) |
| turn passed (all checks) | 40/42 (95.2 %) | 25/27 (92.6 %) | 15/15 (100.0 %) |
| LLM calls per turn | avg 2.5, p50 2.0, p95 5.0, max 5.0 | avg 2.7, p50 2.0, p95 5.0, max 5.0 | avg 2.2, p50 2.0, p95 4.0, max 4.0 |
| refused calls per turn | avg 0.2, p50 0.0, p95 2.0, max 2.0 | avg 0.3, p50 0.0, p95 2.0, max 2.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 |
| fallback (Groq) calls per turn | avg 0.0, p50 0.0, p95 0.0, max 0.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 |
| turn seconds | avg 18.3, p50 13.5, p95 54.0, max 67.6 | avg 21.0, p50 14.8, p95 57.1, max 67.6 | avg 13.4, p50 12.1, p95 31.7, max 31.7 |

## New failures (1)

- m1_8_language_turns:L20: all checks pass

## Known failing (1)

- m1_10_known_failing:K04 [from M1.7, M1.8]: reply_must_mention: does not mention 'Gym'; reply_must_mention: does not mention 'Call'

## Fixed (known failing, now passing) (13)

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
- m1_10_known_failing:K05 [from M1.8]: all checks pass
- m1_10_known_failing:K06 [from M1.8]: all checks pass
- m1_10_known_failing:K07 [from M1.8]: all checks pass

## Refused calls (7)

- m1_7_calendar_turns:t08: cancel_event (needs approval)
- m1_7_calendar_turns:t10: cancel_event (needs approval), cancel_event (needs approval)
- m1_8_language_turns:I02: cancel_event (needs approval), cancel_event (needs approval)
- m1_10_known_failing:K04: cancel_event (needs approval), cancel_event (needs approval)

## Turns

| turn | lang | verdict | routing | tools | reply | refused | llm_calls | turn_s |
|---|---|---|---|---|---|---|---|---|
| m1_7_calendar_turns:t01 | hinglish | pass | ok | ok | ok | 0 | 2 | 14.4 |
| m1_7_calendar_turns:t02 | en | pass | ok | ok | ok | 0 | 2 | 13.9 |
| m1_7_calendar_turns:t03 | hinglish | pass | ok | ok | ok | 0 | 2 | 13.5 |
| m1_7_calendar_turns:t04 | en | pass | ok | ok | ok | 0 | 2 | 12.1 |
| m1_7_calendar_turns:t05 | hinglish | fixed | ok | ok | ok | 0 | 4 | 23.6 |
| m1_7_calendar_turns:t06 | en | pass | ok | ok | ok | 0 | 4 | 23.6 |
| m1_7_calendar_turns:t07 | hinglish | fixed | ok | ok | ok | 0 | 2 | 15.3 |
| m1_7_calendar_turns:t08 | hinglish | pass | ok | ok | ok | 1 | 5 | 35.5 |
| m1_7_calendar_turns:t09 | hinglish | pass | ok | ok | ok | 0 | 2 | 12.2 |
| m1_7_calendar_turns:t10 | hinglish | fixed | ok | ok | ok | 2 | 5 | 57.1 |
| m1_8_language_turns:L01 | hinglish | pass | ok | ok | ok | 0 | 3 | 19.9 |
| m1_8_language_turns:L02 | en | pass | ok | ok | ok | 0 | 3 | 15.0 |
| m1_8_language_turns:L03 | hinglish | pass | ok | ok | ok | 0 | 2 | 11.8 |
| m1_8_language_turns:L04 | en | pass | ok | ok | ok | 0 | 2 | 10.6 |
| m1_8_language_turns:L05 | hinglish | pass | ok | ok | ok | 0 | 2 | 11.4 |
| m1_8_language_turns:L06 | en | pass | ok | ok | ok | 0 | 2 | 11.0 |
| m1_8_language_turns:L07 | hinglish | pass | ok | ok | ok | 0 | 1 | 5.6 |
| m1_8_language_turns:L08 | en | fixed | ok | ok | ok | 0 | 1 | 5.2 |
| m1_8_language_turns:L09 | hinglish | pass | ok | ok | ok | 0 | 2 | 12.1 |
| m1_8_language_turns:L10 | en | pass | ok | ok | ok | 0 | 2 | 11.3 |
| m1_8_language_turns:L11 | hinglish | pass | ok | ok | ok | 0 | 2 | 14.8 |
| m1_8_language_turns:L12 | en | pass | ok | ok | ok | 0 | 2 | 13.9 |
| m1_8_language_turns:L13 | hinglish | fixed | ok | ok | ok | 0 | 2 | 13.5 |
| m1_8_language_turns:L14 | en | pass | ok | ok | ok | 0 | 2 | 12.1 |
| m1_8_language_turns:L15 | hinglish | pass | ok | ok | ok | 0 | 2 | 15.8 |
| m1_8_language_turns:L16 | en | pass | ok | ok | ok | 0 | 2 | 13.4 |
| m1_8_language_turns:L17 | hinglish | fixed | ok | ok | ok | 0 | 2 | 15.9 |
| m1_8_language_turns:L18 | en | pass | ok | ok | ok | 0 | 4 | 31.7 |
| m1_8_language_turns:L19 | hinglish | pass | ok | ok | ok | 0 | 2 | 11.9 |
| m1_8_language_turns:L20 | hinglish | fail | ok | - | FAIL | 0 | 2 | 9.9 |
| m1_8_language_turns:I01 | hinglish | pass | ok | ok | ok | 0 | 2 | 12.2 |
| m1_8_language_turns:I02 | hinglish | fixed | ok | ok | ok | 2 | 5 | 67.6 |
| m1_8_language_turns:I03 | hinglish | pass | ok | ok | ok | 0 | 4 | 33.5 |
| m1_8_language_turns:I04 | hinglish | pass | ok | ok | ok | 0 | 2 | 12.4 |
| m1_8_language_turns:I05 | en | pass | ok | ok | ok | 0 | 2 | 11.1 |
| m1_10_known_failing:K01 | en | fixed | ok | ok | ok | 0 | 2 | 10.5 |
| m1_10_known_failing:K02 | hinglish | fixed | ok | ok | ok | 0 | 4 | 28.5 |
| m1_10_known_failing:K03 | hinglish | fixed | ok | ok | ok | 0 | 2 | 15.8 |
| m1_10_known_failing:K04 | hinglish | known_failing | ok | ok | FAIL | 2 | 5 | 54.0 |
| m1_10_known_failing:K05 | en | fixed | ok | ok | ok | 0 | 1 | 5.2 |
| m1_10_known_failing:K06 | hinglish | fixed | ok | ok | ok | 0 | 2 | 12.3 |
| m1_10_known_failing:K07 | hinglish | fixed | ok | ok | ok | 0 | 2 | 16.8 |

## Comparison

Before: evals/reports/m1.10_eval_2026-11-23_run1.json (Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); commit 9a826ab)
After: evals/reports/m1_exit_eval_2026-11-23_run4.json (Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); commit 575e084)

Code changed between 9a826ab and 575e084.

| metric | group | before | after |
|---|---|---|---|
| routing accuracy | all | 40/42 (95.2 %) | 42/42 (100.0 %) |
| routing accuracy | hinglish | 25/27 (92.6 %) | 27/27 (100.0 %) |
| routing accuracy | en | 15/15 (100.0 %) | 15/15 (100.0 %) |
| tool-call accuracy | all | 35/41 (85.4 %) | 41/41 (100.0 %) |
| tool-call accuracy | hinglish | 21/26 (80.8 %) | 26/26 (100.0 %) |
| tool-call accuracy | en | 14/15 (93.3 %) | 15/15 (100.0 %) |
| reply checks (all) | all | 35/42 (83.3 %) | 40/42 (95.2 %) |
| reply checks (all) | hinglish | 20/27 (74.1 %) | 25/27 (92.6 %) |
| reply checks (all) | en | 15/15 (100.0 %) | 15/15 (100.0 %) |
| reply: language | all | 42/42 (100.0 %) | 41/42 (97.6 %) |
| reply: language | hinglish | 27/27 (100.0 %) | 26/27 (96.3 %) |
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
| turn passed (all checks) | all | 34/42 (81.0 %) | 40/42 (95.2 %) |
| turn passed (all checks) | hinglish | 20/27 (74.1 %) | 25/27 (92.6 %) |
| turn passed (all checks) | en | 14/15 (93.3 %) | 15/15 (100.0 %) |
| LLM calls per turn | all | avg 3.1, p50 3.0, p95 7.0, max 7.0 | avg 2.5, p50 2.0, p95 5.0, max 5.0 |
| LLM calls per turn | hinglish | avg 3.3, p50 3.0, p95 7.0, max 7.0 | avg 2.7, p50 2.0, p95 5.0, max 5.0 |
| LLM calls per turn | en | avg 2.8, p50 3.0, p95 4.0, max 4.0 | avg 2.2, p50 2.0, p95 4.0, max 4.0 |
| refused calls per turn | all | avg 0.1, p50 0.0, p95 1.0, max 1.0 | avg 0.2, p50 0.0, p95 2.0, max 2.0 |
| refused calls per turn | hinglish | avg 0.1, p50 0.0, p95 1.0, max 1.0 | avg 0.3, p50 0.0, p95 2.0, max 2.0 |
| refused calls per turn | en | avg 0.1, p50 0.0, p95 1.0, max 1.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 |
| fallback (Groq) calls per turn | all | avg 0.0, p50 0.0, p95 0.0, max 0.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 |
| fallback (Groq) calls per turn | hinglish | avg 0.0, p50 0.0, p95 0.0, max 0.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 |
| fallback (Groq) calls per turn | en | avg 0.0, p50 0.0, p95 0.0, max 0.0 | avg 0.0, p50 0.0, p95 0.0, max 0.0 |
| turn seconds | all | avg 10.7, p50 9.9, p95 30.3, max 31.2 | avg 18.3, p50 13.5, p95 54.0, max 67.6 |
| turn seconds | hinglish | avg 11.7, p50 10.1, p95 30.7, max 31.2 | avg 21.0, p50 14.8, p95 57.1, max 67.6 |
| turn seconds | en | avg 8.9, p50 9.0, p95 14.1, max 14.1 | avg 13.4, p50 12.1, p95 31.7, max 31.7 |

Turns whose verdict changed: 8

- m1_7_calendar_turns:t10: known_failing -> fixed
- m1_8_language_turns:L13: known_failing -> fixed
- m1_8_language_turns:L17: known_failing -> fixed
- m1_8_language_turns:L20: pass -> fail
- m1_8_language_turns:I02: known_failing -> fixed
- m1_10_known_failing:K05: known_failing -> fixed
- m1_10_known_failing:K06: known_failing -> fixed
- m1_10_known_failing:K07: known_failing -> fixed

Newly failing turns: 1

- m1_8_language_turns:L20: routing

## Details

### m1_7_calendar_turns:t01 (hinglish): pass

**You:** Kal subah 10 baje Rahul ke saath meeting daal do

**Leo:** Ho gaya! 'Meeting with Rahul' Tue 17 Nov, 10:00-11:00 am calendar mein daal diya.

Language: Hindi markers: ['ho', 'gaya', 'mein', 'daal', 'diya']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 250 tok 3.2/5.3 s, agent:ollama 399 tok 7.6/8.7 s

Tool calls:
- `create_event({'title': 'Meeting with Rahul', 'start': '2026-11-17T10:00:00+05:30', 'end': '2026-11-17T11:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-17T10:00:00+05:30', 'end': '2026-11-17T11:00:00+05:30', 'title': 'Meeting with Rahul'}`

### m1_7_calendar_turns:t02 (en): pass

**You:** Add a dentist appointment on Thursday at 4:30 pm

**Leo:** Done! Added 'Dentist Appointment' on Thu 19 Nov, 4:30-5:30 pm.

Language: Hindi markers outside tool data: []
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 247 tok 3.0/5.2 s, agent:ollama 370 tok 7.5/8.7 s

Tool calls:
- `create_event({'title': 'Dentist Appointment', 'start': '2026-11-19T16:30:00+05:30', 'end': '2026-11-19T17:30:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-19T16:30:00+05:30', 'end': '2026-11-19T17:30:00+05:30', 'title': 'Dentist Appointment'}`

### m1_7_calendar_turns:t03 (hinglish): pass

**You:** Thursday dopahar free hoon?

**Leo:** Thu 19 Nov ko aap free ho: 12:00-1:00 pm aur 2:00-4:00 pm.

Language: Hindi markers: ['ko', 'aap', 'ho', 'aur']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 242 tok 3.0/4.9 s, agent:ollama 375 tok 7.6/8.6 s

Tool calls:
- `find_free_slots({'start': '2026-11-19T12:00:00+05:30', 'end': '2026-11-19T16:00:00+05:30'})` -> `[{'start': '2026-11-19T12:00:00+05:30', 'end': '2026-11-19T13:00:00+05:30'}, {'start': '2026-11-19T14:00:00+05:30', 'end': '2026-11-19T16:00:00+05:30'}]`

### m1_7_calendar_turns:t04 (en): pass

**You:** Am I free tomorrow evening?

**Leo:** You're free on Tue 17 Nov: 4:00-8:00 pm.

Language: Hindi markers outside tool data: []
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 240 tok 2.9/4.6 s, agent:ollama 369 tok 6.5/7.5 s

Tool calls:
- `find_free_slots({'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T20:00:00+05:30'})` -> `[{'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T20:00:00+05:30'}]`

### m1_7_calendar_turns:t05 (hinglish): fixed

**You:** 3 baje wali meeting 5 baje kar do

**Leo:** 3 baje ke baad ke meeting ko 5 baje tak kar diya gaya.

Language: Hindi markers: ['baje', 'ke', 'ke', 'ko', 'baje', 'tak', 'kar', 'diya', 'gaya']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 246 tok 3.1/5.3 s, agent:ollama 399 tok 2.5/3.4 s, agent:ollama 501 tok 5.4/7.1 s, responder:ollama 394 tok 6.0/7.8 s

Tool calls:
- `get_events({'start': '2026-11-16T00:00:00+05:30', 'end': '2026-11-17T00:00:00+05:30'})` -> `[{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T15:00:00+05:30', 'end': '2026-11-16T16:00:00+05:30'}]`
- `move_event({'event_id': 'mock-evt-team', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'})` -> `{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}`

### m1_7_calendar_turns:t06 (en): pass

**You:** Move my 3 pm meeting to 5 pm

**Leo:** Done! Your meeting is now at 5:00 pm.

Language: Hindi markers outside tool data: []
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 244 tok 3.0/4.8 s, agent:ollama 394 tok 5.5/6.4 s, agent:ollama 496 tok 5.5/7.8 s, responder:ollama 372 tok 3.2/4.5 s

Tool calls:
- `get_events({'start': '2026-11-16T00:00:00+05:30', 'end': '2026-11-17T00:00:00+05:30'})` -> `[{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T15:00:00+05:30', 'end': '2026-11-16T16:00:00+05:30'}]`
- `move_event({'event_id': 'mock-evt-team', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'})` -> `{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}`

### m1_7_calendar_turns:t07 (hinglish): fixed

**You:** Saturday ko kya kya hai?

**Leo:** Saturday ko gym 8 baje se 9 baje tak hai, aur call 10 baje se 10:30 baje tak hai.

Language: Hindi markers: ['ko', 'baje', 'se', 'baje', 'tak', 'hai', 'aur', 'baje', 'se', 'baje', 'tak', 'hai']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: agent:ollama 352 tok 5.9/6.8 s, responder:ollama 386 tok 5.4/8.5 s

Tool calls:
- `get_events({'start': '2026-11-21T00:00:00+05:30', 'end': '2026-11-22T00:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`

### m1_7_calendar_turns:t08 (hinglish): pass

**You:** Saturday ka gym cancel kar do

**Leo:** Gym cancel karne ka request na kiya gaya, user ko approval chahiye pehle.

Language: Hindi markers: ['ka', 'kiya', 'gaya', 'ko', 'chahiye']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 240 tok 2.8/4.3 s, agent:ollama 360 tok 5.0/5.9 s, agent:ollama 538 tok 8.7/10.1 s, agent:ollama 584 tok 3.5/5.5 s, responder:ollama 475 tok 7.6/9.7 s

Tool calls:
- `get_events({'start': '2026-11-21T00:00:00+05:30', 'end': '2026-11-22T00:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`
- `cancel_event({'event_id': 'mock-evt-gym'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`

### m1_7_calendar_turns:t09 (hinglish): pass

**You:** Kal Rahul ke saath meeting

**Leo:** Kal matlab aane wala kal (tomorrow) ya beeta hua kal (yesterday)?

Language: Hindi markers: ['kal', 'matlab', 'wala', 'kal', 'hua', 'kal']
Plan: [['calendar']]; stops: {'calendar': 'ask'}
LLM calls: supervisor:ollama 240 tok 2.8/4.4 s, responder:ollama 374 tok 5.9/7.8 s

Tool calls:
- none

### m1_7_calendar_turns:t10 (hinglish): fixed

**You:** Agar Saturday ko baarish nahi hogi to subah 7 baje Lonavala trip plan kar do, aur Saturday subah clear kar do.

**Leo:** Agar Saturday ko baarish nahi hogi to 7 baje Lonavala trip plan kar diya gaya hai. Saturday subah ke events ko clear karne ka kamaal nahi kiya gaya, user ke sanad par hai.

Language: Hindi markers: ['agar', 'ko', 'nahi', 'hogi', 'baje', 'kar', 'diya', 'gaya', 'hai', 'ke', 'ko', 'ka', 'nahi', 'kiya', 'gaya', 'ke', 'hai']
Plan: [['research', 'calendar']]; stops: {'research': 'done', 'calendar': 'done'}
LLM calls: supervisor:ollama 268 tok 3.6/7.2 s, agent:ollama 300 tok 6.1/7.2 s, agent:ollama 402 tok 5.5/13.5 s, agent:ollama 450 tok 8.6/10.5 s, responder:ollama 606 tok 13.6/18.7 s

Tool calls:
- `get_weather({'place': 'Lonavala'})` -> `{'place': 'Lonavala, Maharashtra, India', 'days': [{'date': '2026-11-21', 'day': 'Saturday', 'rain_chance_pct': 5, 'rain_mm': 0.0}], 'source': 'Open-Meteo', 'source_url': 'https://open-meteo.com'}`
- `get_events({'start': '2026-11-21T06:00:00+05:30', 'end': '2026-11-21T12:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`
- `cancel_event({'event_id': 'mock-evt-gym'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`
- `cancel_event({'event_id': 'mock-evt-call'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`
- `create_event({'title': 'Lonavala Trip - 7 AM Saturday', 'start': '2026-11-21T07:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-21T07:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30', 'title': 'Lonavala Trip - 7 AM Saturday'}`

### m1_8_language_turns:L01 (hinglish): pass

**You:** Kal Pune mein baarish hogi?

**Leo:** No, kal Pune mein baarish nahi hogi. 70% chance of rain tomorrow (Open-Meteo).

Language: Hindi markers: ['kal', 'mein', 'nahi', 'hogi']
Plan: [['research']]; stops: {'research': 'done'}
LLM calls: supervisor:ollama 243 tok 2.9/4.4 s, agent:ollama 255 tok 4.3/5.3 s, responder:ollama 430 tok 7.7/10.1 s

Tool calls:
- `get_weather({'place': 'Pune'})` -> `{'place': 'Pune, Maharashtra, India', 'days': [{'date': '2026-11-16', 'day': 'today', 'rain_chance_pct': 10, 'rain_mm': 0.0}, {'date': '2026-11-17', 'day': 'tomorrow', 'rain_chance_pct': 70, 'rain_mm': 6.2}, {'date': '2026-11-21', 'day': 'Saturday', 'rain_chance_pct': 5, 'rain_mm': 0.0}], 'source': 'Open-Meteo', 'source_url': 'https://open-meteo.com'}`

### m1_8_language_turns:L02 (en): pass

**You:** Will it rain in Pune tomorrow?

**Leo:** Yes, it is likely to rain in Pune tomorrow, with a 70% chance (Open-Meteo).

Language: Hindi markers outside tool data: []
Plan: [['research']]; stops: {'research': 'done'}
LLM calls: supervisor:ollama 241 tok 2.9/4.5 s, agent:ollama 254 tok 4.3/5.3 s, responder:ollama 408 tok 3.1/5.3 s

Tool calls:
- `get_weather({'place': 'Pune'})` -> `{'place': 'Pune, Maharashtra, India', 'days': [{'date': '2026-11-16', 'day': 'today', 'rain_chance_pct': 10, 'rain_mm': 0.0}, {'date': '2026-11-17', 'day': 'tomorrow', 'rain_chance_pct': 70, 'rain_mm': 6.2}, {'date': '2026-11-21', 'day': 'Saturday', 'rain_chance_pct': 5, 'rain_mm': 0.0}], 'source': 'Open-Meteo', 'source_url': 'https://open-meteo.com'}`

### m1_8_language_turns:L03 (hinglish): pass

**You:** Doodh ko meri tasks list mein daal do

**Leo:** 'Doodh' aapki tasks list mein daal diya.

Language: Hindi markers: ['aapki', 'mein', 'daal', 'diya']
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 246 tok 3.2/5.2 s, agent:ollama 343 tok 5.5/6.6 s

Tool calls:
- `add_task({'title': 'Doodh'})` -> `{'id': 3, 'title': 'Doodh', 'done': False}`

### m1_8_language_turns:L04 (en): pass

**You:** Add bread to my tasks

**Leo:** Added 'bread' to your tasks.

Language: Hindi markers outside tool data: []
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 239 tok 3.0/4.7 s, agent:ollama 334 tok 4.9/5.8 s

Tool calls:
- `add_task({'title': 'bread'})` -> `{'id': 3, 'title': 'bread', 'done': False}`

### m1_8_language_turns:L05 (hinglish): pass

**You:** Milk wala task complete kar do

**Leo:** 'Buy milk' task complete mark kar diya.

Language: Hindi markers: ['kar', 'diya']
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 242 tok 2.8/5.0 s, agent:ollama 340 tok 5.4/6.4 s

Tool calls:
- `complete_task({'title': 'milk'})` -> `{'id': 1, 'title': 'Buy milk', 'done': True}`

### m1_8_language_turns:L06 (en): pass

**You:** Mark the electricity bill task as done

**Leo:** Marked 'Pay electricity bill' as done.

Language: Hindi markers outside tool data: []
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 241 tok 2.8/4.9 s, agent:ollama 339 tok 5.0/6.1 s

Tool calls:
- `complete_task({'title': 'electricity bill'})` -> `{'id': 2, 'title': 'Pay electricity bill', 'done': True}`

### m1_8_language_turns:L07 (hinglish): pass

**You:** 2450 ka 18 percent kitna hai?

**Leo:** 18% of 2450 ka jawab 441 hai.

Language: Hindi markers: ['ka', 'hai']
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 247 tok 3.1/5.2 s

Tool calls:
- `calculate({'expression': '18% of 2450'})` -> `{'expression': '18% of 2450', 'computed': '(18/100)*2450', 'result': '441'}`

### m1_8_language_turns:L08 (en): fixed

**You:** What is 15% of 3200?

**Leo:** 15% of 3200 = 480.

Language: Hindi markers outside tool data: []
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 247 tok 3.2/5.2 s

Tool calls:
- `calculate({'expression': '15% of 3200'})` -> `{'expression': '15% of 3200', 'computed': '(15/100)*3200', 'result': '480'}`

### m1_8_language_turns:L09 (hinglish): pass

**You:** Chai ke liye 10 minute ka timer laga do

**Leo:** 'chai' ka timer 10 minute ke liye laga diya.

Language: Hindi markers: ['ka', 'ke', 'liye', 'diya']
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 248 tok 3.2/5.0 s, agent:ollama 344 tok 5.5/7.0 s

Tool calls:
- `start_timer({'minutes': 10.0, 'label': 'chai'})` -> `{'label': 'chai', 'minutes': 10.0, 'ends_at': '2026-11-14T08:10:00+05:30'}`

### m1_8_language_turns:L10 (en): pass

**You:** Set a 5 minute timer for the eggs

**Leo:** Timer 'eggs' set for 5 minutes.

Language: Hindi markers outside tool data: []
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 243 tok 2.9/4.8 s, agent:ollama 339 tok 5.0/6.5 s

Tool calls:
- `start_timer({'minutes': 5.0, 'label': 'eggs'})` -> `{'label': 'eggs', 'minutes': 5.0, 'ends_at': '2026-11-14T08:05:00+05:30'}`

### m1_8_language_turns:L11 (hinglish): pass

**You:** Kal subah 10 baje Rahul ke saath meeting daal do

**Leo:** Ho gaya! 'Meeting with Rahul' Tue 17 Nov, 10:00-11:00 am calendar mein daal diya.

Language: Hindi markers: ['ho', 'gaya', 'mein', 'daal', 'diya']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 250 tok 3.1/5.1 s, agent:ollama 399 tok 8.6/9.7 s

Tool calls:
- `create_event({'title': 'Meeting with Rahul', 'start': '2026-11-17T10:00:00+05:30', 'end': '2026-11-17T11:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-17T10:00:00+05:30', 'end': '2026-11-17T11:00:00+05:30', 'title': 'Meeting with Rahul'}`

### m1_8_language_turns:L12 (en): pass

**You:** Add a dentist appointment on Thursday at 4:30 pm

**Leo:** Done! Added 'Dentist Appointment' on Thu 19 Nov, 4:30-5:30 pm.

Language: Hindi markers outside tool data: []
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 247 tok 3.1/5.2 s, agent:ollama 370 tok 7.5/8.7 s

Tool calls:
- `create_event({'title': 'Dentist Appointment', 'start': '2026-11-19T16:30:00+05:30', 'end': '2026-11-19T17:30:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-19T16:30:00+05:30', 'end': '2026-11-19T17:30:00+05:30', 'title': 'Dentist Appointment'}`

### m1_8_language_turns:L13 (hinglish): fixed

**You:** Thursday dopahar free hoon?

**Leo:** Thu 19 Nov ko aap free ho: 12:00-1:00 pm aur 2:00-4:00 pm.

Language: Hindi markers: ['ko', 'aap', 'ho', 'aur']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 242 tok 3.0/4.9 s, agent:ollama 375 tok 7.6/8.6 s

Tool calls:
- `find_free_slots({'start': '2026-11-19T12:00:00+05:30', 'end': '2026-11-19T16:00:00+05:30'})` -> `[{'start': '2026-11-19T12:00:00+05:30', 'end': '2026-11-19T13:00:00+05:30'}, {'start': '2026-11-19T14:00:00+05:30', 'end': '2026-11-19T16:00:00+05:30'}]`

### m1_8_language_turns:L14 (en): pass

**You:** Am I free tomorrow evening?

**Leo:** You're free on Tue 17 Nov: 4:00-8:00 pm.

Language: Hindi markers outside tool data: []
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 240 tok 2.9/4.6 s, agent:ollama 369 tok 6.5/7.5 s

Tool calls:
- `find_free_slots({'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T20:00:00+05:30'})` -> `[{'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T20:00:00+05:30'}]`

### m1_8_language_turns:L15 (hinglish): pass

**You:** Saturday ko kya kya hai?

**Leo:** Saturday ko gym 8 baje se 9 baje tak hai, aur call 10 baje se 10:30 baje tak hai.

Language: Hindi markers: ['ko', 'baje', 'se', 'baje', 'tak', 'hai', 'aur', 'baje', 'se', 'baje', 'tak', 'hai']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: agent:ollama 352 tok 5.9/6.8 s, responder:ollama 386 tok 5.9/9.0 s

Tool calls:
- `get_events({'start': '2026-11-21T00:00:00+05:30', 'end': '2026-11-22T00:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`

### m1_8_language_turns:L16 (en): pass

**You:** What's on my calendar on Thursday?

**Leo:** Lunch with Neha on Thursday 19 Nov, 1:00-2:00 pm.

Language: Hindi markers outside tool data: []
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: agent:ollama 352 tok 6.0/6.9 s, responder:ollama 346 tok 4.3/6.5 s

Tool calls:
- `get_events({'start': '2026-11-19T00:00:00+05:30', 'end': '2026-11-20T00:00:00+05:30'})` -> `[{'id': 'mock-evt-lunch', 'title': 'Lunch with Neha', 'start': '2026-11-19T13:00:00+05:30', 'end': '2026-11-19T14:00:00+05:30'}]`

### m1_8_language_turns:L17 (hinglish): fixed

**You:** Aaj shaam 5 baje kya hai?

**Leo:** Aaj shaam 5 baje hai, 5:00 pm. Calendar mein 'Review call' hai.

Language: Hindi markers: ['aaj', 'baje', 'hai', 'mein', 'hai']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: agent:ollama 391 tok 7.7/8.6 s, responder:ollama 367 tok 5.0/7.3 s

Tool calls:
- `get_events({'start': '2026-11-16T16:00:00+05:30', 'end': '2026-11-16T20:00:00+05:30'})` -> `[{'id': 'mock-evt-review', 'title': 'Review call', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}]`

### m1_8_language_turns:L18 (en): pass

**You:** Move my 5 pm call to 6 pm

**Leo:** Your 5 pm review call is now at 6 pm. Updated in calendar.

Language: Hindi markers outside tool data: []
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 244 tok 3.0/4.8 s, agent:ollama 394 tok 7.6/8.5 s, agent:ollama 572 tok 8.7/10.7 s, responder:ollama 394 tok 6.0/7.5 s

Tool calls:
- `get_events({'start': '2026-11-16T00:00:00+05:30', 'end': '2026-11-17T00:00:00+05:30'})` -> `[{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T15:00:00+05:30', 'end': '2026-11-16T16:00:00+05:30'}, {'id': 'mock-evt-review', 'title': 'Review call', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}]`
- `move_event({'event_id': 'mock-evt-review', 'start': '2026-11-16T18:00:00+05:30', 'end': '2026-11-16T19:00:00+05:30'})` -> `{'id': 'mock-evt-review', 'title': 'Review call', 'start': '2026-11-16T18:00:00+05:30', 'end': '2026-11-16T19:00:00+05:30'}`

### m1_8_language_turns:L19 (hinglish): pass

**You:** Ek note likh lo: gas cylinder book karna hai

**Leo:** Note save kar diya.

Language: Hindi markers: ['kar', 'diya']
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 246 tok 3.2/5.0 s, agent:ollama 341 tok 5.5/6.8 s

Tool calls:
- `add_note({'text': 'gas cylinder book karna hai'})` -> `{'id': 2, 'text': 'gas cylinder book karna hai'}`

### m1_8_language_turns:L20 (hinglish): fail

**You:** Hi Leo, kaise ho?

**Leo:** Hi! Baat karein, kaise ho? 😊

Language: Hindi markers: ['ho']
Plan: [[]]; stops: no agent run
LLM calls: supervisor:ollama 241 tok 2.9/4.3 s, responder:ollama 325 tok 4.3/5.6 s

Tool calls:
- none

### m1_8_language_turns:I01 (hinglish): pass

**You:** Saturday ko free time kab hai?

**Leo:** Sat 21 Nov ko aap free ho: 6:00-8:00 am, 9:00-10:00 am aur 10:30 am-11:00 pm.

Language: Hindi markers: ['ko', 'aap', 'ho', 'aur']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 241 tok 2.8/4.8 s, agent:ollama 349 tok 6.4/7.4 s

Tool calls:
- `find_free_slots({'start': '2026-11-21T06:00:00+05:30', 'end': '2026-11-21T23:00:00+05:30'})` -> `[{'start': '2026-11-21T06:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30'}, {'start': '2026-11-21T09:00:00+05:30', 'end': '2026-11-21T10:00:00+05:30'}, {'start': '2026-11-21T10:30:00+05:30', 'end': '2026-11-21T23:00:00+05:30'}]`

### m1_8_language_turns:I02 (hinglish): fixed

**You:** Agar Saturday ko baarish nahi hogi to subah 7 baje Lonavala trip plan kar do, aur Saturday subah clear kar do.

**Leo:** Agar Saturday ko baarish nahi hogi to 7 baje Lonavala trip plan kar do. Lekin gym aur call events ko clear karne ka kama na hai, user ke saath puchhne padenge pehle.

Language: Hindi markers: ['agar', 'ko', 'nahi', 'hogi', 'baje', 'kar', 'lekin', 'aur', 'ko', 'ka', 'hai', 'ke']
Plan: [['research', 'calendar']]; stops: {'research': 'done', 'calendar': 'done'}
LLM calls: supervisor:ollama 268 tok 3.7/7.8 s, agent:ollama 305 tok 6.0/7.0 s, agent:ollama 486 tok 8.7/17.8 s, agent:ollama 509 tok 10.8/12.4 s, responder:ollama 658 tok 17.4/22.5 s

Tool calls:
- `get_weather({'place': 'Lonavala'})` -> `{'place': 'Lonavala, Maharashtra, India', 'days': [{'date': '2026-11-16', 'day': 'today', 'rain_chance_pct': 10, 'rain_mm': 0.0}, {'date': '2026-11-17', 'day': 'tomorrow', 'rain_chance_pct': 70, 'rain_mm': 6.2}, {'date': '2026-11-21', 'day': 'Saturday', 'rain_chance_pct': 5, 'rain_mm': 0.0}], 'source': 'Open-Meteo', 'source_url': 'https://open-meteo.com'}`
- `get_events({'start': '2026-11-21T06:00:00+05:30', 'end': '2026-11-21T12:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`
- `cancel_event({'event_id': 'mock-evt-gym'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`
- `cancel_event({'event_id': 'mock-evt-call'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`
- `create_event({'title': 'Trip to Lonavala Saturday Morning', 'start': '2026-11-21T07:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-21T07:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30', 'title': 'Trip to Lonavala Saturday Morning'}`

### m1_8_language_turns:I03 (hinglish): pass

**You:** 3 baje wali meeting 4 baje kar do

**Leo:** 3 baje wali meeting 4 baje kar di gayi. Calendar mein update kiya gaya.

Language: Hindi markers: ['baje', 'wali', 'baje', 'kar', 'di', 'gayi', 'mein', 'kiya', 'gaya']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 246 tok 3.2/5.4 s, agent:ollama 399 tok 7.7/8.6 s, agent:ollama 577 tok 8.8/10.9 s, responder:ollama 416 tok 6.5/8.6 s

Tool calls:
- `get_events({'start': '2026-11-16T00:00:00+05:30', 'end': '2026-11-17T00:00:00+05:30'})` -> `[{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T15:00:00+05:30', 'end': '2026-11-16T16:00:00+05:30'}, {'id': 'mock-evt-review', 'title': 'Review call', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}]`
- `move_event({'event_id': 'mock-evt-team', 'start': '2026-11-16T16:00:00+05:30', 'end': '2026-11-16T17:00:00+05:30'})` -> `{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T16:00:00+05:30', 'end': '2026-11-16T17:00:00+05:30'}`

### m1_8_language_turns:I04 (hinglish): pass

**You:** Kal 4 baje dentist appointment daal do

**Leo:** Ho gaya! 'Dentist Appointment' Tue 17 Nov, 4:00-5:00 pm calendar mein daal diya. 4:00 pm hi chahiye tha na?

Language: Hindi markers: ['ho', 'gaya', 'mein', 'daal', 'diya', 'chahiye']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 244 tok 3.0/4.7 s, agent:ollama 363 tok 6.5/7.6 s

Tool calls:
- `create_event({'title': 'Dentist Appointment', 'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T17:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T17:00:00+05:30', 'title': 'Dentist Appointment'}`

### m1_8_language_turns:I05 (en): pass

**You:** Add a haircut tomorrow at 4

**Leo:** Done! Added 'Haircut' on Tue 17 Nov, 4:00-5:00 pm. Did you mean 4:00 pm?

Language: Hindi markers outside tool data: []
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 241 tok 2.9/4.5 s, agent:ollama 359 tok 5.5/6.5 s

Tool calls:
- `create_event({'title': 'Haircut', 'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T17:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-17T16:00:00+05:30', 'end': '2026-11-17T17:00:00+05:30', 'title': 'Haircut'}`

### m1_10_known_failing:K01 (en): fixed

**You:** complete my milk task

**Leo:** Marked 'Buy milk' as done.

Language: Hindi markers outside tool data: []
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 238 tok 2.8/4.5 s, agent:ollama 332 tok 5.0/6.0 s

Tool calls:
- `complete_task({'title': 'milk'})` -> `{'id': 1, 'title': 'Buy milk', 'done': True}`

### m1_10_known_failing:K02 (hinglish): fixed

**You:** 3 baje wali meeting 5 baje kar do

**Leo:** 3 baje ke baad ka meeting 5 baje tak kar diya.

Language: Hindi markers: ['baje', 'ke', 'ka', 'baje', 'tak', 'kar', 'diya']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 246 tok 3.0/5.0 s, agent:ollama 396 tok 7.5/8.4 s, agent:ollama 498 tok 5.5/7.6 s, responder:ollama 394 tok 5.8/7.4 s

Tool calls:
- `get_events({'start': '2026-11-16T00:00:00+05:30', 'end': '2026-11-17T00:00:00+05:30'})` -> `[{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T15:00:00+05:30', 'end': '2026-11-16T16:00:00+05:30'}]`
- `move_event({'event_id': 'mock-evt-team', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'})` -> `{'id': 'mock-evt-team', 'title': 'Team meeting', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}`

### m1_10_known_failing:K03 (hinglish): fixed

**You:** Saturday ko kya kya hai?

**Leo:** Saturday ko gym 8 baje se 9 baje tak hai aur call 10 baje se 10:30 baje tak hai.

Language: Hindi markers: ['ko', 'baje', 'se', 'baje', 'tak', 'hai', 'aur', 'baje', 'se', 'baje', 'tak', 'hai']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: agent:ollama 352 tok 6.4/7.3 s, responder:ollama 386 tok 5.5/8.5 s

Tool calls:
- `get_events({'start': '2026-11-21T00:00:00+05:30', 'end': '2026-11-22T00:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`

### m1_10_known_failing:K04 (hinglish): known_failing

**You:** Agar Saturday ko baarish nahi hogi to subah 7 baje Lonavala trip plan kar do, aur Saturday subah clear kar do.

**Leo:** Agar Saturday ko baarish nahi hogi to, subah 7 baje Lonavala trip plan kar lunga. Saturday ke baare mein clear karne ka plan nahi kiya gaya, kyunki user ne approval diya nahi.

Language: Hindi markers: ['agar', 'ko', 'nahi', 'hogi', 'baje', 'kar', 'ke', 'mein', 'ka', 'nahi', 'kiya', 'gaya', 'diya', 'nahi']
Plan: [['research', 'calendar']]; stops: {'research': 'done', 'calendar': 'done'}
LLM calls: supervisor:ollama 268 tok 3.7/7.8 s, agent:ollama 305 tok 2.4/3.5 s, agent:ollama 486 tok 8.5/18.3 s, agent:ollama 509 tok 2.5/4.1 s, responder:ollama 659 tok 15.0/20.2 s

Tool calls:
- `get_weather({'place': 'Lonavala'})` -> `{'place': 'Lonavala, Maharashtra, India', 'days': [{'date': '2026-11-16', 'day': 'today', 'rain_chance_pct': 10, 'rain_mm': 0.0}, {'date': '2026-11-17', 'day': 'tomorrow', 'rain_chance_pct': 70, 'rain_mm': 6.2}, {'date': '2026-11-21', 'day': 'Saturday', 'rain_chance_pct': 5, 'rain_mm': 0.0}], 'source': 'Open-Meteo', 'source_url': 'https://open-meteo.com'}`
- `get_events({'start': '2026-11-21T06:00:00+05:30', 'end': '2026-11-21T12:00:00+05:30'})` -> `[{'id': 'mock-evt-gym', 'title': 'Gym', 'start': '2026-11-21T08:00:00+05:30', 'end': '2026-11-21T09:00:00+05:30'}, {'id': 'mock-evt-call', 'title': 'Call', 'start': '2026-11-21T10:00:00+05:30', 'end': '2026-11-21T10:30:00+05:30'}]`
- `cancel_event({'event_id': 'mock-evt-gym'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`
- `cancel_event({'event_id': 'mock-evt-call'})` -> `{'error': 'cancel_event needs human approval', 'needs_approval': True}`
- `create_event({'title': 'Check weather for Lonavala on Saturday', 'start': '2026-11-21T07:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30'})` -> `{'id': 'mock-evt-1', 'start': '2026-11-21T07:00:00+05:30', 'end': '2026-11-21T08:00:00+05:30', 'title': 'Check weather for Lonavala on Saturday'}`
- reply check failed: reply_must_mention: does not mention 'Gym'
- reply check failed: reply_must_mention: does not mention 'Call'

### m1_10_known_failing:K05 (en): fixed

**You:** What is 15% of 3200?

**Leo:** 15% of 3200 = 480.

Language: Hindi markers outside tool data: []
Plan: [['productivity']]; stops: {'productivity': 'done'}
LLM calls: supervisor:ollama 247 tok 3.1/5.2 s

Tool calls:
- `calculate({'expression': '15% of 3200'})` -> `{'expression': '15% of 3200', 'computed': '(15/100)*3200', 'result': '480'}`

### m1_10_known_failing:K06 (hinglish): fixed

**You:** Thursday dopahar free hoon?

**Leo:** Thu 19 Nov ko aap free ho: 12:00-1:00 pm aur 2:00-4:00 pm.

Language: Hindi markers: ['ko', 'aap', 'ho', 'aur']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: supervisor:ollama 242 tok 2.9/4.9 s, agent:ollama 375 tok 6.5/7.5 s

Tool calls:
- `find_free_slots({'start': '2026-11-19T12:00:00+05:30', 'end': '2026-11-19T16:00:00+05:30'})` -> `[{'start': '2026-11-19T12:00:00+05:30', 'end': '2026-11-19T13:00:00+05:30'}, {'start': '2026-11-19T14:00:00+05:30', 'end': '2026-11-19T16:00:00+05:30'}]`

### m1_10_known_failing:K07 (hinglish): fixed

**You:** Aaj shaam 5 baje kya hai?

**Leo:** Aaj shaam 5 baje hai, Mon 16 Nov 2026, 5:00 pm. Calendar mein 'Review call' hai.

Language: Hindi markers: ['aaj', 'baje', 'hai', 'mein', 'hai']
Plan: [['calendar']]; stops: {'calendar': 'done'}
LLM calls: agent:ollama 391 tok 7.6/8.5 s, responder:ollama 367 tok 5.0/8.2 s

Tool calls:
- `get_events({'start': '2026-11-16T16:00:00+05:30', 'end': '2026-11-16T20:00:00+05:30'})` -> `[{'id': 'mock-evt-review', 'title': 'Review call', 'start': '2026-11-16T17:00:00+05:30', 'end': '2026-11-16T18:00:00+05:30'}]`

