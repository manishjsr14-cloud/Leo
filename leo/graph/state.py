"""The shared state passed between LangGraph nodes (architecture section 4.1).

Only the fields used so far are declared. Later tasks add fields
(memories, language, intent, ...) when they need them.
"""

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage, convert_to_openai_messages
from langgraph.graph.message import add_messages


class LeoState(TypedDict, total=False):
    """What every node can read and update during one request."""

    messages: Annotated[list[AnyMessage], add_messages]  # the conversation
    next_agent: str  # supervisor's routing decision, or "FINISH"
    plan: list[str]  # one task per supervisor hop, in order
    agent_results: dict[str, Any]  # what each agent found, by agent name
    hops: int  # supervisor -> agent hops so far in this request
    completed_agents: list[str]  # agents that finished this request; never re-chosen


# Turn the state into the plain message list the LLM gateway expects:
# a system prompt, any agent results, then the conversation.
def chat_messages(system_prompt: str, state: LeoState) -> list[dict]:
    messages = [{"role": "system", "content": system_prompt}]
    results = state.get("agent_results") or {}
    if results:
        lines = "\n".join(f"- {name}: {value}" for name, value in results.items())
        messages.append({"role": "system", "content": f"Agent results so far:\n{lines}"})
    return messages + convert_to_openai_messages(state.get("messages", []))
