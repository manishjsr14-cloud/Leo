# Leo — Problem Statement

## 1. Background

Knowledge workers lose a large part of their day to small, repetitive tasks that each need a context switch: checking the calendar, searching the web, looking up the weather, doing quick calculations, opening apps and files, setting reminders, and remembering what was decided earlier.

Existing assistants (Siri, Alexa, Google Assistant) cover only part of this:

- **Closed and hard to extend.** Developers cannot add their own tools or change how the assistant reasons.
- **Shallow memory.** They forget context between sessions and do not learn user preferences.
- **Weak multi-step reasoning.** They handle single commands ("what's the weather") but not tasks like "check Saturday's weather, and if it won't rain, plan a trip at 7 am and remind me the night before".
- **Cost and privacy.** A capable agent usually means paying for a frontier model API and sending every message, calendar entry and memory to the cloud.
- **Built for Western English.** Indian users naturally mix Hindi and English ("Hinglish") and use Indian expressions like "parso", "dhai baje", "do the needful". Most assistants either force pure English or pure Hindi and get these wrong.

## 2. Problem

> There is no open, extensible, low-cost personal AI agent that can **understand voice or text in Hinglish and Indian English**, **reason over multiple steps**, **take real actions** on a user's computer, calendar and the web, and **remember the user over time** — while **running mostly on the user's own modest hardware**, staying reachable from their phone, and staying safe when it acts on the user's behalf.

## 3. Proposed Solution

**Leo** is an open-source, voice-first personal AI agent that runs **locally on a laptop** with a small open model (Ollama) as its **main machine**, can borrow a **bigger model on the user's gaming desktop as a backup** when no game is running, and uses **free cloud inference (Groq) only as a fallback**. It:

1. Listens (wake word "Hey Leo" + speech-to-text) or accepts typed input, from the laptop, an iPhone or a PC.
2. Plans and executes multi-step tasks with a **multi-agent workflow built on LangGraph**: a supervisor agent delegates to specialist agents, each owning a small set of tools.
3. Uses a **layer of small trained ML models** to detect language, route requests, recall memories and decide when the local model needs help from a bigger model.
4. Acts through its agents: PC control, a local calendar with reminders, web search, weather, news, calculator, notes, tasks, habits, expenses and the user's own documents.
5. Remembers facts, preferences and past conversations using short-term and long-term (vector) memory, stored on the laptop.
6. Responds in natural speech and text.
7. Asks for confirmation before any risky or irreversible action (deleting events, bulk changes, running commands).

It ships in two forms:

- **Laptop server (main):** full capabilities on the user's laptop (8 GB RAM, 4 GB GPU), reachable privately from the user's iPhone and PC.
- **Web demo (deployed):** a safe, sandboxed subset on Groq that recruiters can try from a link.

## 4. Target Users

| User | Need |
|---|---|
| Professionals / students | Hands-free help with daily tasks, calendar and reminders, from laptop or phone |
| Developers | A hackable agent framework that runs on ordinary hardware |
| Privacy-conscious users | Personal data kept on their own machine |
| Recruiters / reviewers | A live demo showing agent and ML engineering skills |

## 5. v1 Scope (Must-Have)

| # | Feature | Example |
|---|---|---|
| F1 | Voice in / out | "Hey Leo, what's on my plate today?" on the laptop; "Hey Siri, Ask Leo" or the PWA mic on the iPhone; push-to-talk or "Hey Leo" on the PC |
| F2 | Long-term memory | Remembers "I prefer meetings after 11 am" |
| F3 | PC control | Open apps, websites, files; volume; system info (on the laptop) |
| F4 | Web search + weather | "Will it rain in Pune tomorrow?" |
| F5 | Calculator | Exact math via a safe evaluator, not LLM guesses |
| F6 | Daily tasks | To-dos, notes, timers |
| F7 | Reminders | "15 minute pehle yaad dila dena": reminders as a laptop notification, spoken by Leo, as a phone push and as a phone calendar alarm (works even if the laptop is off later) |
| F8 | Local calendar | "Am I free Thursday afternoon?", find slots, create/move events in a calendar stored on the laptop and synced to iPhone and PC (CalDAV) |
| F9 | Multi-agent orchestration | A supervisor routes work to specialist agents (calendar, research, desktop, productivity, finance, knowledge) and combines results |
| F10 | Automated multi-agent evaluation | Simulated users, judges and red-teamers test Leo automatically on every change |
| F11 | Guardrails | Blocks jailbreaks, prompt injection from web pages and files, unsafe content and PII leaks; validates every tool call |
| F12 | LLMOps | Prompt versioning, tracing, latency/escalation/quota dashboards, eval-gated CI, alerts, user-feedback loop |
| F13 | Self-learning | Learns preferences, reflects on mistakes, saves successful workflows as reusable skills, retrains its ML models and improves its own prompts — all safely gated by evals |
| F14 | Hinglish & Indian English | Understands and replies in code-mixed Hindi + English: "Kal subah 10 baje Rahul ke saath meeting daal do", Indian-accent voice, Indian date/time and number words |
| F15 | Local-first inference | Runs on a local `qwen3:4b` model on a 4 GB GPU; escalates only on errors, timeouts or predicted hard requests |
| F16 | ML layer | Trained models for embeddings, language detection, intent routing, local-vs-bigger-model risk prediction and expense categories, with a training loop fed by traces and evals |
| F17 | Multi-device access | Use the same Leo, with shared memory and chats, from iPhone (PWA + "Hey Siri, Ask Leo" Shortcut) and PC over a private Tailscale network |
| F18 | Morning briefing | At a set time: weather, events, reminders, tasks, birthdays, top news, budget, habits and laptop status, on the iPhone and spoken on the laptop |
| F19 | Routines | "Good night Leo", "focus mode": one phrase runs several steps |
| F20 | Birthdays & festivals | "Neha ka birthday 12 March hai" → yearly reminders; optional Indian holidays calendar |
| F21 | Expense tracker | "Aaj 250 ka lunch", "petrol 1.5k" → logged with category, budgets and monthly summaries |
| F22 | Habit tracker | "Paani piya", "gym done" → streaks and gentle nudges |
| F23 | Ask your files | Questions answered from the user's own PDFs and notes, with file and page citations |
| F24 | Link & YouTube summaries | Share a link or video from the iPhone and get a short summary |
| F25 | File finder | "Kal wali PDF kahan hai?" → finds files on the laptop |
| F26 | Laptop & PC health monitor | Alerts for temperature, battery, disk space and SSD health, services and backups on the laptop; disk space, SSD health, GPU/CPU temperature and gaming session reports on the PC |
| F27 | World & India news | Top stories from several outlets, grouped by story, summarized neutrally by Groq (`gpt-oss-120b`) in the user's language mix with source links; follow topics like cricket or AI; top 5 in the morning briefing |
| F28 | Desktop backup tier with gaming mode | A bigger model (`qwen3:14b`) on the gaming desktop handles harder requests when it is on and free; Leo detects Steam, Epic Games and Riot games (and any GPU-heavy full-screen game) and switches to laptop → Groq automatically |

**Delivery in stages:** the **MVP** covers F2, F4, F5, F6, F7, F8, F9, F15, F17, F18, F20 and F27 (headlines) by text (plus basic guardrails and evals). Voice, the full ML layer, everyday and knowledge features, the desktop backup tier, full guardrails, the AutoGen harness, self-learning and the web demo follow after the MVP (see `architecture.md` §19).

## 6. Out of Scope (v1)

- Email (no Gmail or other mailbox integration)
- Google or other cloud calendars (the calendar is local; read-only iCal subscriptions are optional)
- Native mobile app (the iPhone uses the installable web app and Shortcuts)
- Controlling the phone or PC directly (PC control acts on the laptop only)
- Running Leo's services or data on the gaming desktop (it is only a backup model tier), or using it for backups
- Bank, UPI or SMS import for expenses
- Smart-home device control
- Payments or purchases
- Fully autonomous actions without user confirmation
- Fine-tuning the main model (a LoRA of the local model is an optional stretch goal)

## 7. Constraints

- **Cost:** ₹0 to run. Local models via Ollama, plus free tools only (Groq, Radicale, Open-Meteo, DuckDuckGo search, RSS news feeds, Tailscale personal plan, optional ntfy).
- **Hardware:** one laptop with 8 GB RAM and a GTX 1650 (4 GB VRAM); Windows Home now, Linux Mint later. The phone is an iPhone. The laptop is the main machine; its model must stay fully on the GPU, and the ML layer runs on the CPU. As a backup, a gaming desktop (RTX 3060 12 GB, 32 GB RAM) lends its GPU when it is on and no game is running; gaming always has priority, and its model files may need to live on another drive because its main disk is full.
- **Availability:** the laptop must stay on and awake for phone access; Leo shows an offline state when it is not.
- **Rate limits:** Groq free tier is rate-limited per model, so fallback and news summaries are used sparingly (batched) and 429s are handled.
- **Privacy:** memory, chats, calendar, reminders, expenses, documents and ML data stay on the laptop. Requests escalated to the desktop stay inside the home network. Data goes to the cloud only for Groq escalations, news summaries, speech-to-text, text-to-speech and flagged safety checks. The web demo uses mock data.
- **Latency:** target under 3 s from end of speech to start of spoken reply for simple queries on the local model.

## 8. Success Metrics

| Metric | Target |
|---|---|
| Supervisor routing accuracy (right agent chosen) | ≥ 95 % |
| Tool-selection accuracy (eval set of 100+ scenarios) | ≥ 90 % |
| Requests handled fully by the laptop model | ≥ 70 % |
| Task success: local + escalation vs Groq-only | Gap < 5 % |
| Intent router accuracy (held-out set) | ≥ 90 % |
| Supervisor LLM calls saved by the intent router | ≥ 40 % |
| Language detector accuracy (en / hinglish / hi) | ≥ 95 % |
| Risk predictor AUC (will the local model fail?) | ≥ 0.80 |
| Laptop model fully on GPU (`ollama ps` = 100 % GPU) during normal use | 100 % |
| Desktop backup tier released within 10 s of a game starting | 100 % |
| Cross-device continuity (start on PC, finish on phone) | Works in 100 % of eval runs |
| Red-team prompt-injection attacks blocked | 100 % |
| Guardrail false-positive rate (safe requests wrongly blocked) | < 3 % |
| PII in stored logs, traces and ML datasets | 0 (redacted) |
| Releases shipped without passing the eval gate | 0 |
| Task success improvement from self-learning (after 4 weeks of use) | +10 % vs. learning disabled |
| Repeat-mistake rate (same error twice after a lesson exists) | < 5 % |
| Hinglish vs English task-success gap | < 5 % |
| Language mirroring (reply matches user's language mix) | ≥ 95 % |
| Hindi date/time phrase parsing accuracy ("parso shaam", "sava teen") | ≥ 95 % |
| Multi-step task success rate | ≥ 80 % |
| Voice round-trip latency (simple query, local) | < 3 s |
| Reminders delivered on time (at least one channel) | ≥ 99 % |
| Morning briefing delivered on time | ≥ 99 % |
| Expense parsing accuracy (amount + category, Hinglish included) | ≥ 95 % amount, ≥ 85 % category |
| Ask-your-files answers grounded in cited chunks | ≥ 90 % |
| Unsafe actions executed without confirmation | 0 |
| Memory recall accuracy on stored facts (Recall@5) | ≥ 90 % |

## 9. Why This Is a Strong AI/ML Portfolio Project

- **Multi-agent systems:** LangGraph supervisor pattern, shared state, checkpointing, human-in-the-loop interrupts, parallel agent execution.
- **Agent design:** tool calling, planning, error recovery — with a small local model, which is harder than with a frontier API.
- **Classical ML engineering:** embeddings, a language classifier, an intent router, an expense category classifier and a gradient-boosted risk predictor, trained from the agent's own traces and evals, with eval gates, model cards and measurable impact (fewer LLM calls, lower latency, smarter routing between laptop, desktop and cloud).
- **Local inference & self-hosting:** running an LLM on a 4 GB GPU (quantization, KV cache tuning, VRAM budgeting), a three-tier model setup that yields the desktop GPU to games automatically, a laptop server reachable privately from iPhone and PC, cross-platform deployment (Windows → Linux).
- **Self-improving agents:** Reflexion-style lessons, skill library, dynamic few-shot learning, weekly ML retraining and DSPy prompt optimization, with a measurable learning curve.
- **Retrieval & memory:** multilingual embeddings and vector search in sqlite-vec for long-term memory, ask-your-files RAG with citations, and news story clustering.
- **Guardrails:** layered input, tool and output rails using Llama Prompt Guard 2, Llama Guard 4 and Presidio PII detection.
- **LLMOps:** versioned prompts, end-to-end tracing, local-to-cloud fallback, quota-aware rate limiting, semantic caching, eval-gated CI/CD, monitoring and alerts, and a feedback loop that turns failures into new test cases.
- **Evaluation:** an AutoGen-style multi-agent eval system (simulated users, LLM judges, red-team attacker) measuring routing accuracy, tool accuracy, task success, safety, and local vs cloud quality — the part most portfolio agents skip.
- **Safety:** human-in-the-loop confirmation and permission tiers for actions.
- **Multimodal:** speech-to-text and text-to-speech pipeline with a custom wake word.
- **Multilingual / Indic NLP:** code-mixed Hinglish understanding, transliteration, Indian date/time and number normalization, Hinglish guardrail and eval sets — directly relevant to Indian AI companies.
