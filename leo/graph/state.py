"""The shared state passed between LangGraph nodes (architecture section 4.1).

Only the fields used so far are declared. Later tasks add fields
(memories, intent, ...) when they need them.
"""

import json
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, convert_to_openai_messages
from langgraph.graph.message import add_messages

from leo.graph.result_words import result_in_words


class LeoState(TypedDict, total=False):
    """What every node can read and update during one request."""

    messages: Annotated[list[AnyMessage], add_messages]  # the conversation
    agent_queue: list[str]  # agents the supervisor planned for this request, in order
    plan: list[str]  # one task per supervisor hop, in order
    agent_results: dict[str, Any]  # what each agent found, by agent name
    hops: int  # agents run so far in this request (capped by graph.max_hops)
    completed_agents: list[str]  # agents that said done in this request
    language: str  # "en", "hinglish" or "hi" for the latest message (M1.8)
    memories: list[str]  # recalled long-term facts, hints for the reply (M2.3)
    personal_question: bool  # the recall gate opened for this message (M2.3b)
    turn_kind: str  # "request", "question" or "statement" (M2.3c)


# The text of the user's latest message ("" when there is none).
def latest_user_text(state: LeoState) -> str:
    users = [m for m in state.get("messages", []) if isinstance(m, HumanMessage)]
    return str(users[-1].content) if users else ""


# One short line per earlier agent: its successful results in words (JSON when
# there are none), so a later agent's prompt stays small (M1.8).
def result_lines(results: dict) -> list[str]:
    lines = []
    for name, outcome in results.items():
        if not isinstance(outcome, dict):
            lines.append(f"- {name}: {outcome}")
            continue
        found = [result_in_words(s["tool"], s["result"])
                 or json.dumps(s["result"], ensure_ascii=False)
                 for s in outcome.get("steps", [])
                 if not (isinstance(s.get("result"), dict) and "error" in s["result"])]
        lines.append(f"- {name}: " + ("; ".join(found) or "no result"))
    return lines


# Turn the state into the plain message list the LLM gateway expects:
# a system prompt, any agent results, then the conversation.
def chat_messages(system_prompt: str, state: LeoState) -> list[dict]:
    messages = [{"role": "system", "content": system_prompt}]
    results = state.get("agent_results") or {}
    if results:
        lines = "\n".join(result_lines(results))
        messages.append({"role": "system", "content": f"Agent results so far:\n{lines}"})
    return messages + convert_to_openai_messages(state.get("messages", []))
