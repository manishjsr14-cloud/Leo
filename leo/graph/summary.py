"""The rolling conversation summary (M2.4, architecture section 6.6).

At the end of a turn, when the thread holds more than conversation.summarize_after
messages, the older ones are folded into state["summary"] by one LLM call and
removed from the state; the last conversation.keep_messages stay as they are
(the cut moves forward to a user message, so the recent part starts with one).
Prompts then carry the summary as one system line before the recent messages
(leo/graph/state.py, summary_message). If the call fails, nothing is removed
and the old summary stays. The node runs after the reply has been shown.
"""

import logging
from collections.abc import Callable

from langchain_core.messages import AnyMessage, HumanMessage, RemoveMessage

from leo.graph.state import LeoState
from leo.llm.gateway import LLMUnavailable
from leo.llm.prompts import load_prompt

log = logging.getLogger(__name__)
PROMPT = load_prompt("summary")


# Where the kept recent messages start: `keep` from the end, moved forward to a
# user message (len(messages) when there is none).
def recent_start(messages: list[AnyMessage], keep: int) -> int:
    start = max(len(messages) - keep, 0)
    while start < len(messages) and not isinstance(messages[start], HumanMessage):
        start += 1
    return start


# The messages as "User: ..." / "Leo: ..." lines.
def transcript(messages: list[AnyMessage]) -> str:
    return "\n".join(("User: " if isinstance(m, HumanMessage) else "Leo: ") + str(m.content)
                     for m in messages)


# The summary call's messages: the prompt, then the old summary and the older
# messages as delimited data.
def summary_request(old_summary: str, older: list[AnyMessage]) -> list[dict]:
    data = (f"<summary>\n{old_summary or '(none yet)'}\n</summary>\n"
            f"<conversation>\n{transcript(older)}\n</conversation>")
    return [{"role": "system", "content": PROMPT.render()}, {"role": "user", "content": data}]


# Fold the older messages into the summary when there are more than `limit`
# messages; otherwise (or if the model fails) change nothing.
def summarize_node(state: LeoState, chat: Callable, keep: int, limit: int,
                   force_cloud: bool = False) -> dict:
    messages = state.get("messages", [])
    if len(messages) <= limit:
        return {}
    older = messages[:recent_start(messages, keep)]
    if not older:
        return {}
    try:
        result = chat(summary_request(state.get("summary", ""), older), None, force_cloud)
    except LLMUnavailable as error:
        log.warning("summary call failed, messages kept: %s", error)
        return {}
    text = result.text.strip()
    if not text:
        log.warning("summary call returned nothing, messages kept")
        return {}
    return {"summary": text, "messages": [RemoveMessage(id=m.id) for m in older]}
