"""The supervisor node: plans, once per request, which agents run and in what order.

One LLM call returns {agents, task}: an ordered list of up to 2 known agent
names with no duplicates (empty for plain chat), and one short task for them.
The graph then runs those agents in order and goes to the responder; the
supervisor is not asked again (architecture section 4.3, decision M1.5: the
4B model kept choosing the remaining agent when asked after each agent).
graph.max_hops still caps how many agents run.
M1 exit check (K07): a plain "what is on my calendar then?" question
(leo/language/query_words.py) is planned to the calendar agent by code, with
no LLM call, whenever the calendar agent is on offer.
"""

import logging
from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, Field, create_model, field_validator

from leo.graph.state import LeoState, chat_messages, latest_user_text
from leo.language.query_words import is_calendar_query
from leo.llm.prompts import load_prompt

log = logging.getLogger("leo.graph")

MAX_PLANNED_AGENTS = 2
CALENDAR_QUERY_TASK = "List the user's calendar events for the time in the message."
PROMPT = load_prompt("supervisor")  # prompts/supervisor.yaml: text, agents and examples


# The agent list for the prompt: "- name: what it does", one per line, then
# example requests for the agents on offer (agents not in the file show by name).
def describe_agents(agents: list[str]) -> str:
    known = PROMPT.extra("agents", {})
    lines = [f"- {name}: {known[name]['does']}" if name in known else f"- {name}"
             for name in agents]
    examples = [f'- "{text}" -> ["{name}"]' for name in agents
                for text in known.get(name, {}).get("examples", [])]
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
    if "calendar" in agents and is_calendar_query(latest_user_text(state)):
        log.info("supervisor: calendar query planned by code")
        return {"agent_queue": ["calendar"], "hops": 0,
                "plan": [*state.get("plan", []), CALENDAR_QUERY_TASK]}
    prompt = PROMPT.render(agents=describe_agents(agents))
    result = chat(chat_messages(prompt, state), plan_model(agents), force_cloud)
    if not result.valid:
        log.warning("supervisor plan invalid, answering directly: text=%r", result.text)
        return {"agent_queue": [], "hops": 0}
    plan = result.parsed
    update = {"agent_queue": list(plan.agents), "hops": 0}
    if plan.agents:
        update["plan"] = [*state.get("plan", []), plan.task]
    return update
