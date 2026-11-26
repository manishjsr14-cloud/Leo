"""The memory_recall and memory_write nodes (M2.3, redesigned in M2.3b; section 4.2).

memory_recall runs first. Only a personal question (a question with a
first-person word, leo/language/memory_words.py) gets hints: its message is
embedded once (the embedder caches the vector for the rest of the turn) and the
recall_k nearest memories go to state["memories"], with no similarity
threshold. state["personal_question"] tells the responder to say it does not
know rather than guess, when no agent ran. Other turns get no hints.

memory_write runs after the reply. It reads ONLY the user's latest message
(section 14.7): never agent results, tool output, web pages, files or the
reply. Code decides whether to store: the word trigger picks first-person
statements, and the plan rule (leo/language/memory_events.py) keeps plans and
events out. Every picked fact is stored; one extraction call only proposes its
subject and, when the message has an update cue ("anymore", "chhod diya"),
which of the nearest memories it replaces. Without a cue nothing is replaced.
If that call fails, the fact is still stored, under the subject "general".

Spans carry counts only; memory text and subjects go through tracing.text(),
so with tracing.include_text off no memory text or subject reaches a trace.
"""

import logging
from collections.abc import Callable
from datetime import datetime

from pydantic import BaseModel, Field

from leo.graph.state import LeoState, latest_user_text
from leo.language.memory_events import is_plan_or_event
from leo.language.memory_words import (
    fact_text,
    has_update_cue,
    is_personal_question,
    worth_remembering,
)
from leo.llm.gateway import LLMUnavailable
from leo.llm.prompts import load_prompt
from leo.memory.memories import (
    MemoryBank,
    clean_subject,
    save_memory,
    search_memories,
    top_hints,
)
from leo.ops import tracing

log = logging.getLogger("leo.memory")
PROMPT = load_prompt("memory")


FALLBACK_SUBJECT = "general"


class MemoryDecision(BaseModel):
    """The extraction step's reply: the fact's subject and, on an update cue, the
    number of the listed memory it replaces (0 for none). Both fields are required
    (architecture section 6.6): with defaults, the schema sent to Ollama marked no
    field required and every reply in the first M2.3b check was broken JSON."""

    subject: str = Field(max_length=60)
    replaces: int


# Find the hints for a personal question and put their texts in state["memories"].
def memory_recall_node(state: LeoState, bank: MemoryBank) -> dict:
    text = latest_user_text(state)
    if not text.strip() or not is_personal_question(text):
        return {"memories": [], "personal_question": False}
    with tracing.span("memory search", "span") as span:
        vector = bank.embedder.embed_query(text)
        hints = top_hints(search_memories(bank, vector, bank.cfg.search_k), bank.cfg)
        best = round(hints[0].similarity, 3) if hints else None
        span.update(metadata={"hints": len(hints), "best": best},
                    output=tracing.text([h.text for h in hints]))
    return {"memories": [h.text for h in hints], "personal_question": True}


# The extraction call's messages: the prompt with nearby subjects (and, on an
# update cue, the nearby memories numbered), then the fact as delimited data.
def extraction_messages(fact: str, nearby: list, cue: bool) -> list[dict]:
    subjects = ", ".join(dict.fromkeys(m.subject for m in nearby)) or "none"
    listed = "\n".join(f"{i}. {m.text}" for i, m in enumerate(nearby, 1)) if cue else ""
    system = PROMPT.render(subjects=subjects, memories=listed or "none (no update cue)")
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"<message>\n{fact}\n</message>"}]


# The extraction call's decision, or None when the LLM is unavailable or the
# reply is not valid.
def ask_extraction(chat: Callable, fact: str, nearby: list, cue: bool,
                   force_cloud: bool) -> MemoryDecision | None:
    try:
        result = chat(extraction_messages(fact, nearby, cue), MemoryDecision, force_cloud)
    except LLMUnavailable as error:
        log.warning("memory extraction failed, stored under %s: %s", FALLBACK_SUBJECT, error)
        return None
    return result.parsed if result.valid else None


# Store the user's latest message when code picks it as a lasting fact.
# Returns no state change; `now` gives the time (a test can fix it).
def memory_write_node(state: LeoState, bank: MemoryBank, chat: Callable,
                      force_cloud: bool = False, now: Callable = datetime.now) -> dict:
    text = latest_user_text(state)
    with tracing.span("memory decide", "span") as span:
        if not worth_remembering(text):
            span.update(metadata={"triggered": False})
            return {}
        fact, moment = fact_text(text), now()
        if is_plan_or_event(fact, moment):
            span.update(metadata={"triggered": True, "stored": False, "plan": True})
            return {}
        cue = has_update_cue(fact)
        vector = bank.embedder.embed_query(text)  # statements are not embedded by recall
        nearby = search_memories(bank, vector, bank.cfg.candidate_subjects)
        decision = ask_extraction(chat, fact, nearby, cue, force_cloud)
        key = (clean_subject(decision.subject) if decision else None) or FALLBACK_SUBJECT
        pick = decision.replaces if decision and cue else 0
        replaces = [nearby[pick - 1].id] if 1 <= pick <= len(nearby) else []
        _, replaced = save_memory(bank, key, fact, state.get("language") or "en", moment,
                                  replaces)
        span.update(metadata={"triggered": True, "stored": True, "cue": cue,
                              "replaced": len(replaced), "fallback": decision is None},
                    output=tracing.text({"subject": key, "fact": fact}))
    return {}
