"""The supervisor node: plans, once per request, which agents run and in what order.

One LLM call returns {agents, task}: an ordered list of up to 2 known agent
names with no duplicates (empty for plain chat), and one short task for them.
The graph then runs those agents in order and goes to the responder; the
supervisor is not asked again (architecture section 4.3, decision M1.5: the
4B model kept choosing the remaining agent when asked after each agent).
graph.max_hops still caps how many agents run.
"""

import logging
from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, Field, create_model, field_validator

from leo.graph.state import LeoState, chat_messages

log = logging.getLogger("leo.graph")

MAX_PLANNED_AGENTS = 2

# Kept here until versioned prompt files arrive in M1.8.
SYSTEM_PROMPT = (
    "You are the supervisor of Leo, a personal assistant. Plan which agents must "
    "act on the user's latest request, in order. Use one agent unless the request "
    "clearly needs two. Use an empty list when no agent is needed (plain chat).\n"
    "Agents:\n{agents}\n"
    'Reply only with JSON: {{"agents": [<agent names in order>], "task": "<one '
    'short instruction for the agents>"}}.'
)


# One short line per agent for the prompt (agents without a line show by name only).
AGENT_DESCRIPTIONS = {
    "productivity": "tasks, notes, timers, calculations",
    "research": "web search, reading web pages, weather",
    "calendar": ("the user's own calendar: what is on a day, whether the user is "
                 "free, adding, planning or scheduling an event, meeting or trip at "
                 "a time, moving it, cancelling or clearing events"),
}


# Example requests per agent, shown only when that agent is on offer. None of
# them is a phrase from an eval turn file.
AGENT_EXAMPLES = {
    "calendar": [
        "Mera Wednesday ka schedule batao",
        "Friday ko 11 baje bank jaana hai, calendar mein daal do",
        "Doctor wali meeting hata do",
    ],
}


# The agent list for the prompt: "- name: what it does", one per line, then
# example requests for the agents that have them.
def describe_agents(agents: list[str]) -> str:
    lines = [f"- {name}: {AGENT_DESCRIPTIONS[name]}" if name in AGENT_DESCRIPTIONS
             else f"- {name}" for name in agents]
    examples = [f'- "{text}" -> ["{name}"]' for name in agents
                for text in AGENT_EXAMPLES.get(name, [])]
    return "\n".join(lines + (["Examples:", *examples] if examples else []))


class SupervisorPlan(BaseModel):
    """The supervisor's structured reply: agents to run in order, and their task."""

    agents: list[str] = Field(max_length=MAX_PLANNED_AGENTS)
    task: str

    # The same agent may not appear twice in one plan.
    @field_validator("agents")
    @classmethod
    def no_duplicates(cls, agents: list[str]) -> list[str]:
        if len(set(agents)) != len(agents):
            raise ValueError("an agent may appear only once in the plan")
        return agents


# The plan schema for this request: list items may only be the given agent names.
def plan_model(agents: list[str]) -> type[SupervisorPlan]:
    names = Literal[tuple(agents)]  # type: ignore[valid-type]
    return create_model("SupervisorPlan", __base__=SupervisorPlan,
                        agents=(list[names], Field(max_length=MAX_PLANNED_AGENTS)))


# Plan the request. Returns the state update: agent_queue (the agents to run,
# in order), the task added to plan, and hops reset to 0. With no agents
# registered, or a reply that fails the schema, the queue is empty and the
# responder answers directly.
def supervisor_node(
    state: LeoState,
    chat: Callable,
    agents: list[str],
    force_cloud: bool = False,
) -> dict:
    if not agents:
        return {"agent_queue": [], "hops": 0}
    prompt = SYSTEM_PROMPT.format(agents=describe_agents(agents))
    result = chat(chat_messages(prompt, state), plan_model(agents), force_cloud)
    if not result.valid:
        log.warning("supervisor plan invalid, answering directly: text=%r", result.text)
        return {"agent_queue": [], "hops": 0}
    plan = result.parsed
    update = {"agent_queue": list(plan.agents), "hops": 0}
    if plan.agents:
        update["plan"] = [*state.get("plan", []), plan.task]
    return update
