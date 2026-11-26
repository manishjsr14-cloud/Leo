# Leo — Phase-wise Implementation Plan

Built from `docs/problem_statement.md` and `docs/architecture.md` (v6). Section numbers like §6.2 refer to the architecture file.

The order follows the architecture roadmap (§19): **Phase 0 → M1 → M2 → M3 → M4 = MVP**, then Phases 5–12. Every task ends with something you can run and a test that proves it.

## How to use this plan with Claude Code

1. Do **one task per Claude Code session** (for example `M1.2`). Start a fresh session for the next task.
2. Before each task, update the "Current task" line in `AGENTS.md`.
3. Start each session with this prompt:

   ```
   Read AGENTS.md, IMPLEMENTATION_PLAN.md and the sections of docs/architecture.md
   listed for task <ID>. Work only on task <ID>. First show me the files you plan
   to create or change and the tests you will write. Wait for my OK before coding.
   ```
4. A task is finished only when its "Done when" check passes on your laptop and the work is committed and pushed.
5. If a task turns out too big for one session, ask Claude Code to split it and add the sub-tasks here.

**One change from the roadmap:** the roadmap puts mock tools and evals in M4. This plan starts them in M1 (a few tests per task, with the test cases committed before the code), and M4 only completes the set and adds CI. This is the same habit that worked in the Practo project, and §19 itself says a small eval set starts in the MVP.

---

## Phase 0 — Repository and environment (half a day)

| Task | What to do | Done when |
|---|---|---|
| 0.1 | Create a public repo `leo` under `manishjsr14-cloud` on GitHub, with no README or .gitignore (same as Practo). Clone it to `D:\Projects\Leo` (not inside OneDrive). | `git remote -v` shows the new repo |
| 0.2 | Add `AGENTS.md`, `.gitignore`, `IMPLEMENTATION_PLAN.md`, and both spec files under `docs/`. Do not create `CLAUDE.md`. Commit and push to `main`. | Files visible on GitHub |
| 0.3 | Python 3.12 virtual environment in `.venv`. Create `requirements.txt` with **all MVP dependencies pinned** (list below) and check they install together. | `pip install -r requirements.txt` finishes with no conflicts |
| 0.4 | Install Ollama, pull `qwen3:4b` and build `leo-qwen3` with: `ollama create leo-qwen3 -f deploy/ollama/Modelfile`, set the four `OLLAMA_*` variables (§6.2). | `ollama ps` shows `leo-qwen3` at `100% GPU` after one test prompt |
| 0.5 | Create free accounts and put keys in `.env` (never committed): Groq, Langfuse Cloud. Add `.env.example` with empty values. | `.env.example` committed; `.env` ignored by git |
| 0.6 | Create the folder skeleton from §18, but only the MVP folders: `leo/{graph,agents,tools,llm,memory,language,reminders,routines,news,guardrails,ops,api}`, `tests/`, `evals/scenarios/`, `prompts/`, `config/`, `deploy/windows/`. Add `config.yaml` (from §6.4) and `leo/config.py` (Pydantic-validated). | `pytest` runs (0 tests) and `ruff check .` passes |

Setup commands (PowerShell):

```powershell
mkdir D:\Projects -Force
cd D:\Projects
git clone https://github.com/manishjsr14-cloud/leo.git Leo
cd Leo
mkdir docs
# copy AGENTS.md, .gitignore, IMPLEMENTATION_PLAN.md here; the two spec files into docs\
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
git add .
git commit -m "Add project specs, plan and agent instructions"
git branch -M main
git push -u origin main
```

**MVP dependencies to pin in 0.3:** langgraph, langchain-core, langchain-openai, langgraph-checkpoint-sqlite, openai, pydantic, pydantic-settings, pyyaml, python-dotenv, langfuse, sqlite-vec, sentence-transformers (or onnxruntime), caldav, icalendar, radicale, apscheduler, feedparser, ddgs, trafilatura, httpx, sympy, win11toast, fastapi, uvicorn, websockets, transformers (Prompt Guard 2), pytest, ruff, mypy.

---

## M1 — Core agent on the laptop (text only, CLI)

Read: §4, §6, §9 (tool table), §15.

| Task | What to build | Main files | Done when |
|---|---|---|---|
| M1.1 | **LLM gateway.** One OpenAI-compatible client for Ollama and Groq. Fallback triggers from §6.1 (connection error, timeouts, bad tool call twice, user override). Token and latency logging. Desktop tier left as a config stub. | `leo/llm/gateway.py` | Tests with a fake client show each trigger falls back to Groq; a real prompt answers from `leo-qwen3` |
| M1.2 | **State and graph skeleton.** `LeoState` (§4.1), nodes `supervisor` and `responder` only, supervisor structured output `{next, task}`, max 8 hops. CLI chat loop. | `leo/graph/state.py`, `supervisor.py`, `builder.py`, `cli.py` | `python -m leo.cli` holds a chat; hop limit test passes |
| M1.3 | **Tool layer with real and mock versions.** Tools are plain functions with Pydantic argument schemas and a tier (🟢/🟡/🔴). Mock versions record every call. | `leo/tools/real/`, `leo/tools/mock/`, `leo/tools/registry.py` | Mock tools return fixed data and a call log |
| M1.4 | **Productivity agent:** tasks, notes, timer, calculator (sympy). Data in SQLite tables `tasks`, `notes`. | `leo/agents/productivity.py`, `leo/memory/schema.sql` | "add milk to my tasks", "what is 18% of 2450" work in the CLI; calculator never uses the LLM for math |
| M1.5 | **Research agent:** web search (DuckDuckGo), read page (trafilatura), weather (Open-Meteo). Page text wrapped in untrusted-data delimiters. | `leo/agents/research.py` | "Will it rain in Pune tomorrow?" answers with a source |
| M1.6 | **Indian time and number parser.** Rules for kal, parso, subah/shaam, sava, saadhe, paune, dhai, dedh, lakh/crore; IST default; asks when "kal" is unclear. | `leo/language/time_parser.py`, `numbers.py` | Commit a test file of 60+ phrases **first**, then reach ≥ 95 % on it |
| M1.7 | **Calendar agent on mock calendar** (real Radicale comes in M2): get events, free slots, create, move, cancel. | `leo/agents/calendar.py` | "Kal subah 10 baje Rahul ke saath meeting daal do" creates the right mock event |
| M1.8 | **Hinglish prompts and language mirroring.** Prompts in `prompts/*.yaml` with a version field; few-shot Hinglish examples per agent; simple token-ratio language tag (the trained detector is Phase 6). | `prompts/`, `leo/language/normalize.py` | Hinglish in → Hinglish reply; English in → English reply, on 10 fixed examples |
| M1.9 | **Tracing.** One Langfuse trace per request with spans per node, LLM call and tool call; prompt and model version tags. | `leo/ops/tracing.py` | A CLI request shows as one trace in Langfuse |
| M1.10 | **First eval set.** One runner for every scored turn file in `evals/scenarios/` (M1.7 and M1.8 turns, plus a regression file of known-failing cases; list in `evals/scenarios/m1_10_suite.yaml`): routing, tool name + key args, reply checks, refused calls, LLM calls and time, Hinglish vs English; comparison with an earlier report. Run on mock tools. Commit scenarios before running. | `evals/run_eval.py` | Report file written to `evals/reports/`; numbers reported as they are |

**Order change (2026-11-13):** M1.9 (tracing) is done right after M1.4 and before M1.5, on purpose, so every later task is traced from the start. The task numbers stay as they are.

**Note for M1.1 (from Phase 0 setup):** `qwen3:4b` runs in thinking mode by default, which is slow. The gateway must send `think=false` on every request to the local model and strip any leftover `<think>...</think>` text from replies. Add one test for each: (1) every request built for Ollama carries `think=false`; (2) a reply containing `<think>...</think>` comes back without it.

**M1.7 closure (2026-11-16): done rule not met, closed with known limits.** The done rule set before run4 (pass t01 and t10 and at least 8/10 turns of `evals/scenarios/m1_7_calendar_turns.yaml`) was not met. Run4 scored 7/10 with t01 (the done-when phrase) passing (`evals/reports/m1.7_calendar_check_2026-11-16_run4.md`; earlier runs 3/10, 4/10, 7/10 stay as recorded). The model no longer writes dates or times: code fills them in. Known limits:
- t05 "3 baje wali meeting 5 baje kar do": the model first calls `move_event` with an invented id (refused by the guard), then recovers through `get_events`.
- t07 "Saturday ko kya kya hai?": the model calls `find_free_slots` instead of `get_events`.
- t10 (§4.5 example): only one of the two cancels (gym) is attempted; the call is not.

No more fixes in M1.7.

**Notes for M1.8 (from M1.7 run4):**
- The responder copies the "In words" result line into the reply instead of using it (t01).
- Free-time replies are wrong (t07: the times given do not match the free slots).
- A "day" range starts at midnight; it should use waking hours from `config.yaml`.
- The t10 reply leaves out the event still on the calendar (the call that was not cancelled).

**M1.10 eval cases carried over from M1.7 run4** (failing turns; written into the M1.10 scenario files, committed before the M1.10 run):
- "3 baje wali meeting 5 baje kar do": `get_events`, then `move_event` on the 3 pm event to 5-6 pm, with no write call on an invented id.
- "Saturday ko kya kya hai?": `get_events` for the whole Saturday, no `find_free_slots`.
- "Agar Saturday ko baarish nahi hogi to subah 7 baje Lonavala trip plan kar do, aur Saturday subah clear kar do.": `get_weather`, `create_event` 7-8 am, and `cancel_event` attempted for both morning events, both refused without approval.

**M1.8 closure (2026-11-22): done rule not met, closed with known limits.** The done rule in `evals/scenarios/m1_8_language_turns.yaml` (decided before any run; one fix round allowed) was not met in run1 or run2. All runs were on the gaming desktop (RTX 3060); their timings are not laptop results. Reports: baseline (pre-M1.8 code) `evals/reports/m1.8_language_check_2026-11-22_baseline.md` (L01, L02 failed before any LLM call: model loading, no Groq key) and `..._baseline_run2.md` (the comparison baseline); `..._run1.md`; `..._run2.md`. Run2: language correct 20/20, no Devanagari replies, every single-step turn except L08 used fewer LLM calls than the baseline (writes 4 → 2, reads 4 → 3); average prompt tokens per call, baseline run2 → run2: supervisor 224 → 245, agent 514 → 397, responder 452 → 398. Latency probe (desktop only): `evals/reports/m1.8_latency_probe_2026-11-22.md`. Known limits after run2:
- L08 "What is 15% of 3200?": the model miscopied the expression ("15% of 320 tqdm"); the new number check refused it and the retry was right (reply 480), but the turn used 4 LLM calls, the same as the baseline.
- L13 "Thursday dopahar free hoon?": the reply named only the 2-4 pm slot and left out 12-1 pm.
- L17 "Aaj shaam 5 baje kya hai?": planned to research instead of calendar (as in the baseline).
- I02 (§4.5 example): the calendar agent did not call `create_event` for the 7 am trip, attempted only the gym cancel, and the reply said the trip "plan karne wala hai" without naming Gym or Call.

Also done in the M1.8 session as separate commits: "at <hour>" read by the time parser (M1.6 regression report `evals/reports/m1.6_parser_check_2026-11-22_at_hour.md`; the M1.6 held-out score stays 97.1 %), and move `event_id` filled by code (M1.7 turn-set regression report `evals/reports/m1.7_calendar_check_2026-11-22_movefill.md`; M1.7's recorded score stays 7/10). No more fixes in M1.8.

**M1.10 eval cases carried over from M1.8 run2** (written into the M1.10 scenario files, committed before the M1.10 run):
- "What is 15% of 3200?": `calculate` with an expression holding 15 and 3200 only, on the first attempt.
- "Thursday dopahar free hoon?" (calendar as in the M1.8 turn file): the reply names both free slots, 12-1 pm and 2-4 pm.
- "Aaj shaam 5 baje kya hai?": plan `calendar`, `get_events`, the reply names the 5 pm event.
- The §4.5 example (already carried over from M1.7): `create_event` 7-8 am is attempted, and the reply names every event still on the calendar.

**M1.10 scope change (2026-11-23, agreed before any M1.10 code):** the "12 scenarios" in the M1.10 row are replaced by the suite in `evals/scenarios/m1_10_suite.yaml`: every turn of `m1_7_calendar_turns.yaml` and `m1_8_language_turns.yaml`, and the regression file `evals/scenarios/m1_10_known_failing.yaml` (K01-K07: the M1.4 "already complete" wording and every known limit and carried-over case of M1.7 and M1.8, each marked known_failing with its task). The M1.1 and M1.6 files are not chat turns and are skipped, with the reason in the suite file. The run1 → run2 comparison is a noise check (no code change between them).

**M1.10 closure (2026-11-23): done.** Runner `evals/run_eval.py` (suite `evals/scenarios/m1_10_suite.yaml`, regression file `evals/scenarios/m1_10_known_failing.yaml`, comparison `evals/eval_compare.py`). Both runs were on the laptop (GTX 1650) and are the M1.10 laptop baseline: later eval runs on the laptop are compared with `evals/reports/m1.10_eval_2026-11-23_run1.json`; desktop runs are compared without timing rows. They ran at temperature 0.7 from the model's Ollama parameters (Leo sends no temperature, no seed). Reports: `evals/reports/m1.10_eval_2026-11-23_run1.md` and `..._run2.md` (with `.json`); run2 holds the run1 → run2 comparison, labelled a noise check (no code change between them). Run1 and run2, 42 turns each: pass 28, new failures 0, known_failing 8, fixed 6; routing 40/42, tool-call 35/41, reply checks 35/42, turns passing all checks 34/42 (Hinglish 20/27, English 14/15); refused calls 6 (4 needs approval, 2 calculate errors). Noise check: 0 turns changed verdict, 0 newly failing. Still known failing: §4.5 example (t10, I02, K04), L13/K06, L17/K07, and K05 ("15% of 3200" first calculate miscopied in both runs). Fixed in both runs: t05, t07, L08, K01, K02, K03. L08 shows as fixed because its own M1.8 checks pass, although its first calculate was also refused in both runs; K05 is the case that checks that. Runner bugs found in the first attempt (report written as `m1.md`, timings unrounded) were fixed before run1 (commit 9a826ab); that first output is not in the repository.

**M1 exit check:** the cross-agent example in §4.5 (weather → calendar) runs end to end in the CLI on mock calendar, on the local model.

**M1 exit check closure (2026-11-24): exit rule not met, closed with known limits.** Rule `evals/scenarios/m1_exit_rule.yaml`, committed before any run: K04 (the §4.5 example) fixed in both of two laptop runs, and no turn newly failing against `evals/reports/m1.10_eval_2026-11-23_run1.json`; one fix round. Checked by `evals/m1_exit_check.py`. All runs on the laptop (GTX 1650), through the eval runner (the graph via `cli.run_turn`, mock tools, local model `leo-qwen3`); the interactive CLI itself, which uses the real web and weather tools, was not part of the check.
- Code changes, each in code, not prompts: LLM temperature now an explicit `config.yaml` setting (`llm.primary.temperature: 0.7`, the value used before; Groq unchanged). K04: "clear <range>" done by code (`leo/agents/calendar_clear.py`): `get_events` for the range, then a `cancel_event` per event, refused together for approval; only command forms ("clear kar do", "clear my ...") are clears, questions ("Saturday subah khaali hai?") are not. An "agar"/"if" condition on adding an event is checked by code (`leo/agents/calendar_condition.py`): above `calendar.rain_skip_percent` (40) rain chance, or with no forecast, no event is added; any other condition adds nothing and asks to confirm. K06: free-slot replies written by code, every slot listed. K07: a narrow word rule (`leo/language/query_words.py`) plans "what is on my calendar then?" questions to calendar with no LLM call (the trained intent router stays Phase 6). K05: "X% of Y" expression built by code (`leo/agents/percent.py`).
- Runs: run1, run2 (commit e75f4fa) are kept as they ran but are invalid for the rule: the runner read the plan only from the supervisor's LLM reply, so code-routed turns scored routing as failed (`evals/reports/m1_exit_check_2026-11-23_run1_run2_invalid.md`). Runner fix cb4e490 (measuring tool only; scoring rules and scenario files unchanged): the plan is the agents that actually ran. run3, run4 on the fixed runner: NOT PASSED (`evals/reports/m1_exit_check_2026-11-24_run3_run4.md`): run4's LLM reply for K04 named neither Gym nor Call, and L20 newly failing. Fix round (26a2040): the reply after a clear or a held event is written by code (`leo/graph/calendar_reply.py`: forecast checked, event added with its time, events waiting for approval by name). run5, run6: NOT PASSED (`evals/reports/m1_exit_check_2026-11-24_run5_run6.md`): K04 fixed in both, L20 newly failing in run6.
- Numbers, only from `evals/reports/m1_exit_eval_2026-11-24_run5.md` and `..._run6.md` (42 turns each), run5 / run6: routing 42/42 / 42/42; tool-call 41/41 / 41/41; reply checks 42/42 / 41/42; turns passing all checks 42/42 / 41/42 (Hinglish 27/27 / 26/27, English 15/15 / 15/15); refused calls 7 / 7, all `cancel_event` needing approval. K04 used 4 LLM calls in each run.
- K04 (the §4.5 example) passed in both fix-round runs (run5, run6), with the code-written reply.

Known limits after the M1 exit check:
- L20 "Hi Leo, kaise ho?" failed the language scorer in run6 with the reply "Hi! Baat karein, kaise ho? 😊"; it passed in run5. The reply is valid Hinglish: the scorer is too strict. To be fixed by scorer v2 in the M1 cleanup task (with a fresh check set); the current scorer and turn files stay unchanged.
- The model can give the trip a poor title: in run6 "Check weather for Lonavala on Saturday", which still passes the `title_contains: lonavala` check.
- The condition check knows only "no rain" conditions; any other "agar"/"if" before an add means nothing is added until the user confirms. After a clear, the model is offered only the add or move the message also asks for; other parts of a linked message are not done.

**M1 cleanup (agreed 2026-11-24, before any cleanup code).** One task, one commit per item, in this order; every item with a check set commits the check set before the code. Step 0: `docs/known_limits.md`, a checklist of every known limit recorded so far; each later item ticks its line in the commit that fixes it.
1. Language scorer v2 (`evals/language_scoring_v2.py`; v1 in `evals/m1_8_scoring.py` stays as it is), with a fresh check set of replies labelled en / hinglish / hi; v1 and v2 reported side by side. v2 rule, fixed before the check set was written: "hi" when Devanagari letters are at least the Roman letters; words found in the turn's tool data are not counted; "hinglish" when at least 2 Hindi markers, or markers are at least 20 % of the words (v1's marker list plus common verb and question words, English look-alikes left out); "en" with no markers; anything else "unclear", which fails both.
2. Hinglish gap: one laptop eval run scored with v1 and v2; each Hinglish turn still failing under v2 listed with its reason; fixes proposed only.
3. Warm-up: one tiny request to load the model when Leo starts, with no effect on the conversation; time to first token of the first user turn measured with and without it.
4. Code-written replies for a single successful `get_events` ("what's on"), English and Hinglish, every event with its time, and a "nothing on" reply.
5. Hindi number words up to 100 for amounts only (`leo/language/number_words.py`, never clock hours); phrase file first; both M1.6 phrase sets must still pass, their recorded scores stay. "saath"/"sath" is 60 only right before sau/hazaar/lakh/crore or a rupee word; "sau"/"hazaar" alone are 100/1000.
6. `read_page` connects to the checked address (pinned), Host header and TLS name kept.
7. Temperature: two laptop runs at 0.7 and two at 0.3 on the same commit, compared with each other and with the M1.10 baseline; no code change unless the numbers justify it; the value is the user's decision.

Done rule: after all items, a full eval suite run on the laptop against `evals/reports/m1.10_eval_2026-11-23_run1.json` shows no newly failing turn, judged with scorer v2 on both sides (the baseline's stored replies rescored with v2); v1 numbers reported alongside.

**M1 cleanup closure (2026-11-24): done.** Done check `evals/reports/m1_cleanup_done_check_2026-11-24.md`: PASSED. Final run `evals/reports/m1_cleanup_eval_2026-11-24_final.md` (laptop, GTX 1650, commit a0a3177, temperature 0.7, 42 turns): routing 42/42, tool-call 41/41, reply checks 42/42, turns passing all checks 42/42 under scorer v1 and under v2 (Hinglish 27/27, English 15/15); refused calls 7, all needing approval; newly failing against M1.10 run1: 0 with v2 on both sides (the rule), 0 with v1. Known limits: `docs/known_limits.md`, ticked item by item. Per item, numbers as in the reports:
1. Scorer v2 (`evals/language_scoring_v2.py`): on the 48-reply check set, v1 36/40, v2 47/48 (`m1_cleanup_scorer_check_2026-11-24.md`). r48 (an English reply quoting the user's "kal wali PDF") is wrong under both. v2's extra marker words were chosen after the check set was written, so 47/48 is not an independent measure.
2. Hinglish gap (`m1_cleanup_hinglish_gap_2026-11-24.md`): one run, 27/27 Hinglish and 15/15 English under both scorers; the baseline's 20/27 vs 14/15 came from tool, time and routing checks, not language. The runner records v1 and v2 and names a failed language check.
3. Warm-up (`leo/llm/warmup.py`): first-turn time to first token 9.88 s without, 3.96 s with (averages of 3 cold starts each, `m1_cleanup_warmup_check_2026-11-24.md`).
4. Code-written "what's on" replies (`leo/graph/events_reply.py`), with a "change not made" line when the message asked for a change but only `get_events` ran.
5. Number words 13-99 for amounts (`leo/language/number_words.py`): 44/44; M1.6 phrase file 112/112 and held-out set 34/34 as regression checks; the recorded M1.6 held-out score stays 97.1 % (`m1_cleanup_number_check_2026-11-24.md`).
6. `read_page` pinned to the checked address; unit tests cover it. The live checks could not show a name-mismatch certificate refusal (timeout, then a ConnectError of unreported cause).
7. Temperature: two runs at 0.7 and two at 0.3 on one commit (`m1_cleanup_temperature_compare_2026-11-24.md`, note `..._temperature_note_2026-11-24.md`). **Decision (user): keep 0.7**, because no difference was measured on this suite under scorer v2 (42/42 in all four runs, 0 v2 verdict differences between the temperatures).
- Measuring fixes in this task: `git_state` ignores `evals/reports/` (three temperature runs had recorded "uncommitted changes" from untracked report files only; not rerun); `run_eval --temperature`. Process slips, recorded in their commits: the first item 2 run crashed after a tracked file was edited mid-run (rerun on a clean commit); 300b164 was committed with a ruff error (fixed in 62a54b1). AGENTS.md gained three working rules from these.

**Planned follow-ups from M1.7** (each done with a fresh check written and committed before it runs):
- Done in the M1 exit check, ahead of M2.5: "clear <range>" handled in code, cancels proposed together. The `human_approval` node itself is still M2.5.
- Query words ("kya kya hai", "what's on"): the M1 exit check routes these to calendar by code; offering `get_events` only (no `find_free_slots`) is still open.

---

## M2 — Memory, calendar, reminders, briefing

Read: §4.6, §7, §9.1, §9.2, §9.3, §9.9.

| Task | What to build | Main files | Done when |
|---|---|---|---|
| M2.1 | **Storage base.** One SQLite file in `leo_data/`, WAL mode, `busy_timeout`, one write connection, sqlite-vec loaded. `VectorStore` interface. | `leo/memory/store.py`, `sqlite_vec.py` | Insert and search 1,000 vectors in a test |
| M2.2 | **Embedder.** `multilingual-e5-small` on CPU, each message embedded once. | `leo/ml/embedder.py` | Hinglish and English versions of the same sentence score as near neighbours |
| M2.3 | **Long-term memory.** `memory_recall` and `memory_write` nodes; facts and preferences in `memories` + `vec_memories`. | `leo/graph/builder.py`, `leo/memory/` | Commit 20 memory questions first; Recall@5 measured and reported (target ≥ 90 %) |
| M2.3b | **Memory redesign** (design points below, to be confirmed when the task starts). | `leo/memory/`, `leo/graph/memory_nodes.py`, `leo/language/memory_words.py` | Fresh check sets committed before the code, judged end to end through the real write path |
| M2.4 | **Checkpointing and rolling summary.** `SqliteSaver` per `thread_id`; older turns compressed into a summary. | `leo/graph/builder.py` | Kill the CLI mid-chat, restart, conversation continues |
| M2.5 | **Human approval.** `interrupt()` for every 🔴 tool; approve or reject from the CLI; partial approval as in §4.5 step 5. Audit log table. | `leo/graph/approval.py` | Test: a cancel request never executes without a "yes" |
| M2.6 | **Radicale calendar.** Run Radicale on localhost with a password; swap the Calendar agent from mock to `caldav`; events as `VEVENT`, reminders as `VALARM`/`VTODO`. | `deploy/radicale/`, `leo/tools/real/calendar.py` | Event created by Leo appears as an `.ics` file in `leo_data/calendar/` |
| M2.7 | **Reminder scheduler.** APScheduler with its job store in SQLite; laptop toast (`win11toast`); catch-up for missed reminders marked "late"; delivered flag to avoid duplicates. | `leo/reminders/scheduler.py`, `notify.py`, `catchup.py` | Reminder set for 2 minutes ahead fires; one set before a restart still fires |

**M2.1 closure (2026-11-24): done.** `open_db` (`leo/memory/store.py`) now also loads sqlite-vec (extension loading turned off again right after); the `VectorStore` interface (`add`, `search`) is in the same file; `SqliteVecStore` (`leo/memory/sqlite_vec.py`) keeps one vec0 table per kind of vector, cosine distance, fixed dimension, table names checked against `^vec_[a-z_]+$`. Done-when test `tests/test_vector_store.py::test_thousand_vectors_match_brute_force`: 1,000 random 384-dimension vectors (fixed seed 2026) stored, 20 queries, each top 5 matches a plain-Python brute-force cosine top 5 (near-ties within 1e-5 may swap places; returned distances within 1e-5 of brute force). It passed with the full suite: `ruff check .` clean, `pytest` 490 passed (commit 7d42f40). No speed figures were measured. No `memories`/`vec_memories` tables yet (M2.3) and no embedding size in `config.yaml` yet (M2.2). The one-writer rule (section 7) is documented in `open_db`, not enforced: no guard against a second write connection (user's decision).

**M2.2 closure (2026-11-24): done, with known limits (user's decision).** `leo/ml/embedder.py`: `intfloat/multilingual-e5-small` on the CPU (`embedder.device` accepts only `cpu`), normalized vectors, `query: ` / `passage: ` prefixes from `config.yaml` added by the embedder (tested with a fake model), a bounded per-message vector cache so each message is embedded once (§8.1), and an offline-first load from `models/hf_cache` (project folder on D:, git-ignored). `psutil==7.2.2` pinned for the RAM measurement. The one `real_model` test passed; plain `pytest` skips it. The check set `evals/scenarios/m2_2_embedder_pairs.yaml` (commit 8b23ff9, before the code; pass rule B; kal/parso recorded, not scored) was run once on the laptop: `evals/reports/m2_2_embedder_check_2026-11-24.md` (commit 279a83c). Result: **FAILED under rule B, 24/36 sentences pass**. Failing: g04 (all three) and g11.hi (book vs cancel: 0.887 / 0.874 / 0.943), g10 and g12 (all three; negation: 0.984 / 0.979 / 0.956), g09.en and g09.hi (ordinary far pairs, small margins: 0.770 vs weakest near 0.757; 0.853 vs 0.834). kal/parso pairs scored 0.939-0.989 (by design: dates come from the time parser, §15). One message: 19.9 ms median of 20 (min 18.1, max 39.1), 4 torch threads. Load: 18.6 s, first message after load 51 ms. RAM: +1130 MiB after loading (34 → 1164 MiB), peak working set 1211 MiB, against ~0.5 GB in §16. Cache on disk: 470 MiB. Reload in a fresh process with `HF_HUB_OFFLINE=1`: offline load ok. The run's offline-reload subprocess hit a cp1252 decode error while reading its stderr; stdout and the exit code were still read, and the script now reads that output as UTF-8 (6bfaf08). Open limits are recorded in `docs/known_limits.md` (negation, book vs cancel, g09, RAM); the set and the model were not changed.

**Note for M2.3 (from M2.2, user's decision):** the embedder puts a fact and its negation almost on top of each other ("I don't eat non-veg food" vs "I eat non-veg food": 0.984, `evals/reports/m2_2_embedder_check_2026-11-24.md`). When `memory_write` stores a fact that contradicts an existing fact on the same subject ("eats non-veg" vs "doesn't eat non-veg"), it replaces the old fact instead of adding a second one. Covered by a test.

**M2.3 closure (2026-11-26): done with known limits (user's decision).** Result quoted: the fresh fix-round set's **Recall@5 9/12 = 0.75** (Hinglish 0.57 of 7), below the 0.90 target (`evals/reports/m2_3_memory_check_2026-11-26_fix.md`, laptop, plugged in, commit 4a6f0fc). The original set's 18/20 = 0.90 in the same report is reported but not quoted as the result: that set was seen before the fix-round recall change. The rerun rule written before the rerun ("close with known limits if below 0.90 on both sets") did not cover this split; the user decided to close.
- Built (be28f6e): `memories` + `vec_memories`, `memory_recall` (message embedded once, top `search_k` 5, at most `recall_k` 3 hints at or above `min_similarity`, to the responder only, as a delimited hints block) and `memory_write` (after the reply; a code word rule first, one extraction LLM call only for a picked message; reads only the user's latest message, section 14.7). Memory spans carry no text or subject unless `tracing.include_text`. `leo/config.py` split first (9fbf721, tests unchanged).
- First check (`m2_3_memory_check_2026-11-26.md`, 4aa838a): FAILED, Recall@5 16/20 = 0.80. Every local call timed out and fell back to Groq. Cause found in Ollama's log: Leo's 20 s first-token limit aborted each model load in progress, 75 times (`m2_3_ollama_log_notes_2026-11-26.md`); probes an hour later loaded in 4.9-5.9 s with and without the embedder (`m2_3_timeout_probe_2026-11-26_run2.md`; the first probe report is invalid for that comparison, startswith bug). Why the loads were slow that hour is not known.
- Load fix (1a54935): warm-up waits up to `llm.primary.load_timeout_s` (120 s); a first-token timeout starts at most one background load that is never aborted, and turns go to Groq meanwhile. Report headers now record the power state (8ee8e23).
- Fix round, each a logged change after the fresh set (810082b): embed "subject in words: fact" (a672737); a replaced memory is kept as inactive history with `undo_replacement` (2188e4a); "maine ... chhod di/diya" trigger words (3f14202); `min_similarity` 0.80 -> 0.88 by the fresh set's rule (4a6f0fc, `m2_3_fix_threshold_2026-11-26.md`).
- Rerun, all calls on the local model (`m2_3_memory_check_2026-11-26_fix.md`): at 0.88 the expected fact is a prompt hint for only 6/20 (original) and 0/12 (fresh) questions; the extraction said remember false for 14 of 29 picked lasting facts, so part B ended with 12 active memories of 30 and Recall@5 0.55 (original) / 0.17 (fresh) on that store; all 7 must-not-store messages kept out; F33 got the `tea_preference` key of F19 and replaced the tea fact. Recall adds 56 prompt tokens (median) when hints are given; the recall node takes 17.5 ms, an extraction call 4.41 s; the word rule picks 0 of the 42 M1.10 suite messages, so those turns make no extraction call.
- Process slip: 3af8668 was committed without running `ruff check .` and `pytest` first (both passed at the next commit).
- Open limits: `docs/known_limits.md`, "Long-term memory (M2.3)", marked "open: M2.3b".

**M2.3b — memory redesign (planned; design points to be confirmed when it starts):**
- Store every triggered fact; code rejects plans and events (messages with a date or time), not the model.
- Replace only on an explicit update cue ("anymore", "ab nahi", "chhod di", "moved to"); otherwise add a new memory.
- Recall gated by personal-question cues ("my", "mera", "do I", "kab hai"), passing the top 1-3 without a threshold.
- Judged on fresh check sets written before the code, end to end through the real write path.

**Note for M2.7 and M3 (from M2.1):** when the reminder scheduler (M2.7) and the API (M3) start writing from other threads, all writes go through one shared writer with a lock.
| M2.8 | **Phone push with ntfy.** Delayed messages for reminders within 3 days; generic-text privacy setting. | `leo/reminders/notify.py` | Reminder arrives on the iPhone with the laptop asleep |
| M2.9 | **Birthdays.** `contacts` table; yearly event with day-before and morning reminders. | `leo/agents/calendar.py` | "Neha ka birthday 12 March hai" creates the yearly event |
| M2.10 | **News headlines (MVP version).** `feedparser` every 60 min from `config/news.yaml`; one batched Groq summary call per fetch; cached; plain headlines if Groq fails. No clustering yet (Phase 5a). | `leo/news/fetch.py`, `summarize.py` | "Aaj ki news" answers from the cache with source links |
| M2.11 | **Morning briefing.** Routine engine reading `config/routines.yaml`; parallel fan-out with `Send` (§4.4); ≤ 6 lines; scheduled time; delivered by ntfy. | `leo/routines/engine.py`, `briefing.py` | Briefing arrives on the phone at the set time for 3 days in a row |

**M2 exit check:** the Hinglish example in §15.4 works end to end with the real calendar, and the reminder is delivered on the laptop and the phone.

---

## M3 — Use it from phone and PC

Read: §3 (all), §7 (backups).

| Task | What to build | Main files | Done when |
|---|---|---|---|
| M3.1 | **API.** FastAPI with `/chat`, `/approve`, `/health` and a WebSocket for streaming replies and approval prompts. | `leo/api/app.py`, `ws.py` | Same chat works through the API as in the CLI |
| M3.2 | **Device auth.** `devices` table, per-device tokens stored as hashes, revoke per device, per-device rate limit. | `leo/api/auth.py` | Request without a valid token gets 401; revoked token stops working |
| M3.3 | **Tailscale.** Install on laptop, iPhone and PC; `tailscale cert` for HTTPS; bind Leo and Radicale to the Tailscale interface only; firewall rule. | `deploy/windows/README.md` | `/health` opens from the phone on mobile data, and does not open from outside Tailscale |
| M3.4 | **PWA.** React + Vite + Tailwind: chat, approval buttons, reminder Snooze/Done page, offline state. Add to iPhone Home Screen. | `web/` | Chat started on the PC continues on the phone (same `thread_id`) |
| M3.5 | **Siri Shortcut "Ask Leo"** and Share Sheet shortcut. Steps documented with screenshots. | `docs/iphone_setup.md` | "Hey Siri, Ask Leo" returns a spoken answer |
| M3.6 | **CalDAV sync.** iPhone Calendar and Reminders, Thunderbird on the PC, pointed at Radicale. | `docs/iphone_setup.md` | Event added on the phone is visible to Leo, and the other way round |
| M3.7 | **Run as a service.** NSSM service with restart on failure; power settings from §3.2; healthchecks.io ping every 5 minutes. | `deploy/windows/` | Laptop reboot → Leo answers from the phone without logging in to start it; stopping the service triggers a phone alert |
| M3.8 | **Backups and encryption.** Nightly SQLite online backup + `.ics` folder into an encrypted restic repo; copy to the external drive when plugged in; weekly restore check; Device Encryption or VeraCrypt for `leo_data/`. | `leo/memory/backup.py` | A restore into a temp folder opens and passes a row-count check |

**M3 exit check:** Leo runs for 48 hours as a service and is used from the iPhone and the PC with no manual restarts.

---

## M4 — Minimum safety and quality

Read: §11.2, §12.1, §12.3, §13.3.

| Task | What to build | Main files | Done when |
|---|---|---|---|
| M4.1 | **Input guard.** Llama Prompt Guard 2 (86M) on CPU as the `input_guard` node; length limit. Commit a test set first: 20 attacks (half Hinglish) + 40 safe requests. | `leo/guardrails/input_guard.py`, `config/guardrails.yaml` | Block rate and false-positive rate measured and reported |
| M4.2 | **Action rails.** One wrapper around every tool call: schema validation, tier check, allow-lists, policy rules (> 3 events, recurring series), per-tool daily limits. Fail-closed for 🔴. | `leo/guardrails/action_rails.py` | Tests for each rail in §12.3 except taint tracking (Phase 7) |
| M4.3 | **Complete the eval set to ~30 scenarios** (≥ 40 % Hinglish): routing, tool calls, approvals, injections in a mock web page and a mock `.ics`. | `evals/scenarios/` | `python evals/run_eval.py` writes a report with per-metric numbers |
| M4.4 | **CI.** `.github/workflows/ci.yml`: ruff, mypy, pytest, and the deterministic evals on mock tools with the Groq profile. Groq key as a GitHub secret. | `.github/workflows/ci.yml` | A push shows a green check; a deliberately broken tool test turns it red |
| M4.5 | **README.** What Leo is, how to install, what works, measured numbers copied from `evals/reports/`, known limits. | `README.md` | A fresh clone can be set up by following it |

**Note for M4.1 (from M2.2, user's decision):** the e5 embedder added 1130 MiB of RAM after loading on the laptop, against ~0.5 GB in §16 (`evals/reports/m2_2_embedder_check_2026-11-24.md`). When Prompt Guard 2 is added, measure torch's share of that RAM and decide torch vs ONNX Runtime for both models (embedder and Prompt Guard 2) together.

**MVP is done when** (§19.1): Leo runs as a service for 2 weeks, is used daily from phone and PC, delivers reminders on time, and CI evals pass. Tag `v0.1-mvp`.

---

## After the MVP

Break each phase into tasks the same way when you reach it; details will be clearer after two weeks of daily use.

| Phase | Deliverable | Read | Exit check |
|---|---|---|---|
| 5 | Voice: "Hey Leo" on the laptop (openWakeWord, webrtcvad, Groq Whisper, edge-tts), PWA mic, PC push-to-talk client, offline voice mode, Desktop agent | §5, §9 | Simple voice query under 3 s to first spoken word |
| 5a | Expense tracker + category classifier, habit tracker, good-night and focus routines, festival calendar, laptop health monitor, news clustering and followed topics | §9.2–9.5, §9.8, §9.9 | Expense parsing ≥ 95 % amount, ≥ 85 % category on a pre-committed set |
| 5b | Ask-your-files RAG with citations, link and YouTube summaries, file finder | §9.6, §9.7 | ≥ 90 % of answers grounded in cited chunks |
| 5c | Desktop backup tier: `qwen3:14b`, `leo-desktop-agent`, game detection, gaming mode, PC health | §6.7, §9.8 | Desktop released within 10 s of a game starting |
| 6 | ML layer v1: language detector, intent router, supervisor skip | §8.1–8.3 | Detector ≥ 95 %, router ≥ 90 %, ≥ 40 % supervisor calls saved |
| 7 | Full guardrails: Llama Guard 4 on flag, context rails, taint tracking, output guard, Presidio with Indian PII | §12 | 100 % of red-team injections blocked, false positives < 3 % |
| 8 | AG2 eval harness (simulator, judges, red team), local vs Groq runs, risk predictor | §11, §8.4 | Risk predictor AUC ≥ 0.80; nightly eval runs on the laptop |
| 9 | Self-learning L1–L4, feedback signals, Groq teacher, review card, compliance checks, bootstrapping | §14 | Repeat-mistake rate < 5 % |
| 10 | Web demo (Groq profile), dashboards, alerts, quota manager, semantic cache, demo video | §10, §13 | Demo link works with mock data only |
| 11 | Weekly ML retraining, DSPy prompt optimization, lesson-to-code, learning dashboard, on/off ablation | §14, §8.5 | +10 % task success with learning on vs off |
| 12 | Leo-4B (L7): dataset builder, public Leo-4B on synthetic data (Google Colab) → eval gate → release on Hugging Face + Ollama; then private Leo-4B on real data (desktop RTX 3060, after 4–8 weeks of use) as the laptop's main model | §14.9, §6.7 | Passes the §14.9 eval gate, incl. 0 personal data reproduced in the memorization check |

**Note for Phase 5 (from M1.8):** speech-to-text may produce Devanagari even with the Hinglish prompt hint. M1.8 tags Devanagari input `hi` and leaves it as it is (no transliteration dependency), so transliteration (§15.2, e.g. `indic-transliteration`) may be needed then; adding it is a new pinned dependency and needs approval.

---

## Things to decide before you start

1. **Backup drive:** the architecture says a pen drive labelled `LEO_BACKUP`. If you will use an external hard disk instead, only the label and wording in M3.8 change.
2. **Windows or Linux Mint first:** this plan assumes Windows, as the architecture does. If you install Linux Mint before starting, Phase 0 commands, the toast library (M2.7) and the service step (M3.7, systemd instead of NSSM) change; nothing else does.
3. **Public repo:** Practo is public and this plan copies that. `leo_data/`, `.env` and `datasets/` are git-ignored so no personal data is pushed. Say so if you would rather keep Leo private until the MVP.
