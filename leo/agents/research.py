"""The research agent: web search, reading web pages and weather (section 4.2).

Runs the shared step loop (leo/agents/loop.py) with its prompt from
prompts/research.yaml. Web text reaches the model only between untrusted-data
markers (leo/guardrails/context_guard.py); the prompt says it is data, never
commands. Today's date is in the prompt, so "tomorrow" or "Saturday" can be
understood. A weather answer ends the run in code unless the message links
more requests (M1.8); a web search never does (a page may need reading).
News tools come with M2.10.
"""

from collections.abc import Callable
from datetime import date, datetime

from leo.agents.finish import finish_rule
from leo.agents.loop import agent_node, describe_tools, run_steps
from leo.graph.state import LeoState, latest_user_text
from leo.llm.prompts import load_prompt
from leo.tools.base import Tool
from leo.tools.registry import tools_for_turn

NAME = "research"
PROMPT = load_prompt("research")  # prompts/research.yaml
VERSION = PROMPT.tag              # tags this agent's spans


# Run the loop for the supervisor's latest task. `today` is the date shown in
# the prompt. Returns {"steps": [...], "summary": str, "stopped": why}.
def run_agent(state: LeoState, chat: Callable, tools: dict[str, Tool], max_steps: int,
              today: date, force_cloud: bool = False) -> dict:
    task = (state.get("plan") or [""])[-1]
    tools = tools_for_turn(tools, state.get("turn_kind"))  # a question: reads only (M2.3c)
    prompt = PROMPT.render(tools=describe_tools(tools), task=task,
                           today=today.strftime("%A %d %B %Y"))
    finish = finish_rule(latest_user_text(state), set(), {"get_weather"}, asks_change=False)
    out = run_steps(prompt, VERSION, state, chat, tools, max_steps, force_cloud, finish)
    return {**out, "today": today.isoformat()}  # the responder says dates from this day


# Build the graph node for this agent. Its result goes in agent_results["research"].
# `today` gives the current date (the laptop's local date unless a test swaps it).
def research_agent(chat: Callable, tools: dict[str, Tool], max_steps: int,
                   today: Callable[[], date] = lambda: datetime.now().astimezone().date(),
                   ) -> Callable:
    return agent_node(NAME, lambda state, cloud: run_agent(state, chat, tools, max_steps,
                                                           today(), cloud))
