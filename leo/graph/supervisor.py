"""The supervisor node: picks the next agent for a request, or finishes.

Structured output {next, task} (architecture section 4.2). The loop
supervisor -> agent -> supervisor stops at graph.max_hops (section 4.3).
An agent that already finished this request (listed in completed_agents) is
left out of the output schema, so the LLM cannot choose it again; when no
agent is left, the supervisor finishes without calling the LLM.
"""

import logging
from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, create_model

from leo.graph.state import LeoState, chat_messages

log = logging.getLogger("leo.graph")

FINISH = "FINISH"

# Kept here until versioned prompt files arrive in M1.8.
SYSTEM_PROMPT = (
    "You are the supervisor of Leo, a personal assistant. Decide which agent "
    "should act next on the user's latest request, or FINISH if the request is "
    "answered or no agent is needed.\n"
    "Agents: {agents}.\n"
    'Reply only with JSON: {{"next": "<agent name or FINISH>", "task": "<one short '
    'instruction for that agent>"}}.'
)


class SupervisorDecision(BaseModel):
    """The supervisor's structured reply."""

    next: str
    task: str


# The decision schema for this turn: `next` may only be one of `agents` or FINISH.
def decision_model(agents: list[str]) -> type[SupervisorDecision]:
    choices = Literal[(*agents, FINISH)]  # type: ignore[valid-type]
    return create_model("SupervisorDecision", __base__=SupervisorDecision,
                        next=(choices, ...))


# Decide the next step. Returns the state update: next_agent, and for a real
# agent also the new task in plan and one more hop. Calls the LLM only when
# some agent has not finished this request yet and the hop limit is not reached.
def supervisor_node(
    state: LeoState,
    chat: Callable,
    agents: list[str],
    max_hops: int,
    force_cloud: bool = False,
) -> dict:
    hops = state.get("hops", 0)
    done = set(state.get("completed_agents") or [])
    agents = [name for name in agents if name not in done]
    if not agents:
        return {"next_agent": FINISH}
    if hops >= max_hops:
        log.warning("hop limit reached: hops=%s max_hops=%s", hops, max_hops)
        return {"next_agent": FINISH}
    prompt = SYSTEM_PROMPT.format(agents=", ".join(agents))
    result = chat(chat_messages(prompt, state), decision_model(agents), force_cloud)
    decision = result.parsed if result.valid else None
    if decision is None or decision.next not in agents:
        log.warning("supervisor finished: valid=%s text=%r", result.valid, result.text)
        return {"next_agent": FINISH}
    return {
        "next_agent": decision.next,
        "plan": [*state.get("plan", []), decision.task],
        "hops": hops + 1,
    }
