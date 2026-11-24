# Known limits

Every known limit recorded in `IMPLEMENTATION_PLAN.md` and `evals/reports/` up to the
M1 cleanup task (2026-11-24), with its source. Numbers are quoted only from the reports.

- `- [x] ... (fixed in <task/commit>)`: fixed.
- `- [ ] ... (open)` or `- [ ] ... (fixed by <task>)`: not fixed yet.
- `- [x] ... (by design: <reason>)`: kept on purpose.

Each M1 cleanup item ticks its line in the commit that fixes it.

## Model and hardware

- [x] Plain `qwen3:4b` is thinking-only: thinking cannot be turned off (`m1.1_think_probe_2026-11-12.md`) (fixed in M1.1, b1fe523: `leo-qwen3` built from the instruct build)
- [x] Plain `qwen3:4b` spilled 28 % to the CPU; `leo-qwen3` measured 100 % GPU, 3145 MiB of 4096 MiB (`m1.1_model_check_2026-11-12.md`) (fixed in M1.1, b1fe523)
- [x] Cold start: the first request waits for the model to load; first token 8.39 s cold, 2.16 s warm (`m1.1_model_check_2026-11-12.md`, laptop); in the first M1.8 baseline (desktop) L01 and L02 failed before any LLM call: model loading, no Groq key (plan, M1.8 closure) (fixed in M1 cleanup item 3: `leo/llm/warmup.py`, one tiny request when the CLI starts, `llm.primary.warm_up`)
- [x] Gaming-desktop (RTX 3060) timings are never quoted as laptop results; the M1.8 runs and the latency probe ran on the desktop (by design: the laptop is the target machine)
- [x] Desktop tier is a `config.yaml` stub; the gateway never calls it (by design: Phase 5c)
- [x] Only one model is ever loaded in Ollama; embeddings, guards and ML models go on the CPU (by design: 8 GB RAM, 4 GB GPU)

## Language

- [x] A Hinglish question got a Devanagari reply (`m1.5_cli_check_2026-11-16_run2.md`) (fixed in M1.8, 567d16e: M1.8 run2 had no Devanagari replies, language correct 20/20)
- [x] Held-out phrase h18 "in an hour remind me" not understood; held-out score 33/34 (97.1 %) (`m1.6_heldout_check_2026-11-15.md`) (fixed in M1.6, 4e0ab19; the recorded score stays 97.1 %)
- [x] "at <hour>" without am/pm not read as a clock time (fixed in M1.8 session, 4858aa7; `m1.6_parser_check_2026-11-22_at_hour.md`)
- [ ] Hindi number words only go up to twelve (ek ... barah) in `leo/language/numbers.py` (fixed by M1 cleanup item 5)
- [ ] Speech-to-text may give Devanagari; Devanagari input is tagged `hi` and left as it is, no transliteration (plan, note for Phase 5) (open: Phase 5, new dependency needs approval)
- [x] The language tag is a simple token ratio, not a trained detector (by design: the detector is Phase 6)

## Agents and tools

- [x] M1.7 t05 "3 baje wali meeting 5 baje kar do": first `move_event` used an invented id (fixed in M1.8 session, 9d199b4: code fills the move `event_id`; t05 passes in M1.10 run1 and run2)
- [x] M1.7 t07 "Saturday ko kya kya hai?": `find_free_slots` called instead of `get_events` (fixed by the M1.8 changes: passes in M1.10 run1 and run2)
- [x] §4.5 example (t10, I02, K04): no `create_event` for the 7 am trip, only the gym cancel attempted (fixed in the M1 exit check, 25ae243 and 26a2040: K04 passed in run5 and run6)
- [x] M1.8 L08 / K05 "What is 15% of 3200?": the first `calculate` miscopied the expression in M1.8 run2 and in M1.10 run1 and run2 (fixed in the M1 exit check, af2c9ff: expression built by code; K05 passed in run5 and run6)
- [x] M1.8 L17 / K07 "Aaj shaam 5 baje kya hai?": planned to research instead of calendar (fixed in the M1 exit check, d13ecfa: narrow word rule; passed in run5 and run6)
- [ ] Query words ("kya kya hai", "what's on"): routed to calendar by code, but the agent is still offered `find_free_slots` as well as `get_events` (plan, planned follow-ups from M1.7) (open)
- [ ] The condition check knows only "no rain" conditions; any other "agar"/"if" before an add adds nothing until the user confirms (plan, M1 exit closure) (open)
- [ ] After a clear, the model is offered only the add or move the message also asks for; other parts of a linked message are not done (plan, M1 exit closure) (open)
- [ ] `read_page` checks the host's addresses, but httpx resolves the name again when connecting, so DNS rebinding is not stopped (`leo/tools/real/web.py` docstring) (fixed by M1 cleanup item 6)
- [ ] The `human_approval` node does not exist yet: 🔴 calls are refused with "needs approval" (fixed by M2.5)
- [x] Calendar is a mock until Radicale (by design: M2.6)
- [x] Query routing is a narrow word rule, not a trained intent router (by design: Phase 6)

## Replies

- [x] The responder copied the "In words" result line into the reply (M1.7 run4 t01, plan notes for M1.8) (fixed in M1.8, 567d16e: no `no_in_words` failure in M1.10 run1 or run2)
- [x] A "day" range started at midnight instead of waking hours (plan notes for M1.8) (fixed in M1.8, 567d16e: `calendar.waking_hours`)
- [x] Free-time replies were wrong or incomplete: M1.7 t07, M1.8 L13 / K06 named only 2-4 pm, not 12-1 pm (fixed in the M1 exit check, 05db9b4: code-written free-slot replies; K06 passed in run5 and run6)
- [x] The §4.5 reply left out the events still on the calendar; in M1 exit run4 the LLM reply named neither Gym nor Call (fixed in the M1 exit fix round, 26a2040: code-written reply; K04 passed in run5 and run6)
- [x] M1.4 "already complete" wording after a task was completed (K01) (fixed in M1.8, 567d16e: code replies; K01 passes in M1.10 run1 and run2)
- [ ] The model can give the trip a poor title: "Check weather for Lonavala on Saturday" in run6, which still passes `title_contains: lonavala` (plan, M1 exit closure) (open)
- [x] Replies to "what's on" questions (a successful `get_events`) are written by the LLM responder, which can leave events out (fixed in M1 cleanup item 4: `leo/graph/events_reply.py`, every event with its time, English and Hinglish, and a "nothing on" reply)
- [ ] If the calendar agent stops after a single `get_events` on a message that asked for a change, the code reply lists the events and does not say the change was not made (found while writing M1 cleanup item 4) (open)

## Measuring

- [x] L20 "Hi Leo, kaise ho?" failed the language scorer in run6 with the valid Hinglish reply "Hi! Baat karein, kaise ho? 😊"; it passed in run5 (`m1_exit_check_2026-11-24_run5_run6.md`) (fixed in M1 cleanup item 1: scorer v2, `evals/language_scoring_v2.py`; v1 unchanged)
- [x] An eval report lists a turn that failed only the language check with the reason "all checks pass" (run6, L20 under "New failures") (fixed in M1 cleanup item 2: reasons name the language check; the comparison no longer calls it "routing")
- [ ] Eval runs use temperature 0.7 with no seed, so verdicts can flip between runs with no code change (L20: pass in run5, fail in run6) (fixed by M1 cleanup item 7: experiment)
- [x] M1 exit run1 and run2 scored code-routed turns as wrong routing: the runner read the plan only from the supervisor's LLM reply (`m1_exit_check_2026-11-23_run1_run2_invalid.md`) (fixed in cb4e490)
- [x] First M1.10 runner output: report file name cut to `m1.md`, timings unrounded (fixed in 9a826ab; that output is not in the repository)
- [x] L08 shows as fixed in M1.10 although its first `calculate` was refused in both runs (by design: K05 is the case that checks the first attempt)
- [ ] The M1 exit check ran through the eval runner on mock tools; the interactive CLI with the real web and weather tools was not part of it (plan, M1 exit closure) (open)
