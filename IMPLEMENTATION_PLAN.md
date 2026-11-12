# Leo — Phase-wise Implementation Plan

Built from `docs/problem_statement.md` and `docs/architecture.md` (v6). Section numbers like §6.2 refer to the architecture file.

The order follows the architecture roadmap (§19): **Phase 0 → M1 → M2 → M3 → M4 = MVP**, then Phases 5–11. Every task ends with something you can run and a test that proves it.

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
| 0.4 | Install Ollama, pull `qwen3:4b`, set the four `OLLAMA_*` variables (§6.2). | `ollama ps` shows `100% GPU` after one test prompt |
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
| M1.10 | **First eval set.** 12 scenarios in `evals/scenarios/` (routing + tool name + key args), run on mock tools. Commit scenarios before running. | `evals/run_eval.py` | Report file written to `evals/reports/`; numbers reported as they are |

**Note for M1.1 (from Phase 0 setup):** `qwen3:4b` runs in thinking mode by default, which is slow. The gateway must send `think=false` on every request to the local model and strip any leftover `<think>...</think>` text from replies. Add one test for each: (1) every request built for Ollama carries `think=false`; (2) a reply containing `<think>...</think>` comes back without it.

**M1 exit check:** the cross-agent example in §4.5 (weather → calendar) runs end to end in the CLI on mock calendar, on the local model.

---

## M2 — Memory, calendar, reminders, briefing

Read: §4.6, §7, §9.1, §9.2, §9.3, §9.9.

| Task | What to build | Main files | Done when |
|---|---|---|---|
| M2.1 | **Storage base.** One SQLite file in `leo_data/`, WAL mode, `busy_timeout`, one write connection, sqlite-vec loaded. `VectorStore` interface. | `leo/memory/store.py`, `sqlite_vec.py` | Insert and search 1,000 vectors in a test |
| M2.2 | **Embedder.** `multilingual-e5-small` on CPU, each message embedded once. | `leo/ml/embedder.py` | Hinglish and English versions of the same sentence score as near neighbours |
| M2.3 | **Long-term memory.** `memory_recall` and `memory_write` nodes; facts and preferences in `memories` + `vec_memories`. | `leo/graph/builder.py`, `leo/memory/` | Commit 20 memory questions first; Recall@5 measured and reported (target ≥ 90 %) |
| M2.4 | **Checkpointing and rolling summary.** `SqliteSaver` per `thread_id`; older turns compressed into a summary. | `leo/graph/builder.py` | Kill the CLI mid-chat, restart, conversation continues |
| M2.5 | **Human approval.** `interrupt()` for every 🔴 tool; approve or reject from the CLI; partial approval as in §4.5 step 5. Audit log table. | `leo/graph/approval.py` | Test: a cancel request never executes without a "yes" |
| M2.6 | **Radicale calendar.** Run Radicale on localhost with a password; swap the Calendar agent from mock to `caldav`; events as `VEVENT`, reminders as `VALARM`/`VTODO`. | `deploy/radicale/`, `leo/tools/real/calendar.py` | Event created by Leo appears as an `.ics` file in `leo_data/calendar/` |
| M2.7 | **Reminder scheduler.** APScheduler with its job store in SQLite; laptop toast (`win11toast`); catch-up for missed reminders marked "late"; delivered flag to avoid duplicates. | `leo/reminders/scheduler.py`, `notify.py`, `catchup.py` | Reminder set for 2 minutes ahead fires; one set before a restart still fires |
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
| 11 | Weekly ML retraining, DSPy prompt optimization, lesson-to-code, learning dashboard, on/off ablation; stretch: LoRA | §14, §8.5 | +10 % task success with learning on vs off |

---

## Things to decide before you start

1. **Backup drive:** the architecture says a pen drive labelled `LEO_BACKUP`. If you will use an external hard disk instead, only the label and wording in M3.8 change.
2. **Windows or Linux Mint first:** this plan assumes Windows, as the architecture does. If you install Linux Mint before starting, Phase 0 commands, the toast library (M2.7) and the service step (M3.7, systemd instead of NSSM) change; nothing else does.
3. **Public repo:** Practo is public and this plan copies that. `leo_data/`, `.env` and `datasets/` are git-ignored so no personal data is pushed. Say so if you would rather keep Leo private until the MVP.
