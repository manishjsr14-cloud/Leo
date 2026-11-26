"""The memory_recall and memory_write nodes (M2.3, architecture section 4.2).

memory_recall runs first: it embeds the user's message (once; the embedder
caches the vector for the rest of the turn), finds the search_k nearest
memories and keeps at most recall_k at or above min_similarity as hints in
state["memories"]. Only the responder shows them to the model.

memory_write runs after the reply. It reads ONLY the user's latest message
(section 14.7): never agent results, tool output, web pages, files or the
reply. A code word rule (leo/language/memory_words.py) decides first, so most
turns make no LLM call; only a picked message goes to one extraction call,
which says whether it is a lasting fact and gives its subject. The nearest
stored subjects are shown to that call, so a fact on the same subject reuses
the key and replaces the old fact (leo/memory/memories.py).

Spans carry counts only; memory text and subjects go through tracing.text(),
so with tracing.include_text off no memory text or subject reaches a trace.
"""

import logging
from collections.abc import Callable
from datetime import datetime

from pydantic import BaseModel, Field

from leo.graph.state import LeoState, latest_user_text
from leo.language.memory_words import fact_text, worth_remembering
from leo.llm.gateway import LLMUnavailable
from leo.llm.prompts import load_prompt
from leo.memory.memories import (
    MemoryBank,
    clean_subject,
    pick_hints,
    save_memory,
    search_memories,
)
from leo.ops import tracing

log = logging.getLogger("leo.memory")
PROMPT = load_prompt("memory")


class MemoryDecision(BaseModel):
    """The extraction step's reply: keep the message as a memory, and under which subject."""

    remember: bool
    subject: str = Field(default="", max_length=60)


# Find the hints for this message and put their texts in state["memories"].
def memory_recall_node(state: LeoState, bank: MemoryBank) -> dict:
    text = latest_user_text(state)
    if not text.strip():
        return {"memories": []}
    with tracing.span("memory search", "span") as span:
        vector = bank.embedder.embed_query(text)
        found = search_memories(bank, vector, bank.cfg.search_k)
        hints = pick_hints(found, bank.cfg)
        best = round(found[0].similarity, 3) if found else None
        span.update(metadata={"found": len(found), "hints": len(hints), "best": best},
                    output=tracing.text([h.text for h in hints]))
    return {"memories": [h.text for h in hints]}


# The extraction call's messages: the prompt with nearby subjects, then the
# fact as delimited data.
def extraction_messages(fact: str, subjects: list[str]) -> list[dict]:
    system = PROMPT.render(subjects=", ".join(subjects) or "none")
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"<message>\n{fact}\n</message>"}]


# Decide whether the user's latest message is a lasting fact and store it.
# Returns no state change; `now` gives the time stamp (a test can fix it).
def memory_write_node(state: LeoState, bank: MemoryBank, chat: Callable,
                      force_cloud: bool = False, now: Callable = datetime.now) -> dict:
    text = latest_user_text(state)
    with tracing.span("memory decide", "span") as span:
        if not worth_remembering(text):
            span.update(metadata={"triggered": False})
            return {}
        fact = fact_text(text)
        vector = bank.embedder.embed_query(text)  # the vector recall made, from the cache
        nearby = search_memories(bank, vector, bank.cfg.candidate_subjects)
        try:
            result = chat(extraction_messages(fact, [m.subject for m in nearby]),
                          MemoryDecision, force_cloud)
        except LLMUnavailable as error:
            log.warning("memory extraction failed, nothing stored: %s", error)
            span.update(metadata={"triggered": True, "stored": False, "error": "unavailable"})
            return {}
        decision = result.parsed if result.valid else None
        key = clean_subject(decision.subject) if decision and decision.remember else None
        if key is None:
            span.update(metadata={"triggered": True, "stored": False,
                                  "remember": bool(decision and decision.remember)})
            return {}
        _, replaced = save_memory(bank, key, fact, state.get("language") or "en", now())
        span.update(metadata={"triggered": True, "stored": True, "replaced": replaced},
                    output=tracing.text({"subject": key, "fact": fact}))
    return {}
