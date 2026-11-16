"""The productivity agent: tasks, notes, timers and the calculator (section 4.2).

Runs the shared step loop (leo/agents/loop.py) with its own prompt and tools.
Choosing the right agent (or FINISH) is the supervisor's job.
"""

from collections.abc import Callable

from leo.agents.loop import agent_node, describe_tools, run_steps, run_tool, step_model
from leo.graph.state import LeoState
from leo.ops import tracing
from leo.tools.base import Tool

NAME = "productivity"

# Kept here until versioned prompt files arrive in M1.8.
SYSTEM_PROMPT = (
    "You are Leo's productivity agent. You manage the user's to-do tasks and "
    "notes, start timers and do arithmetic, only through these tools:\n{tools}\n"
    'Reply only with JSON: either {{"<tool name>": {{<its arguments>}}}} to use one '
    'tool, or {{"done": {{"summary": "<what you did and the results>"}}}} when '
    "finished.\n"
    'Rules: a task title is just the item, e.g. "milk" for "add milk to my tasks". '
    'To complete a task by name, pass its title, e.g. complete_task(title="milk"). '
    "For any arithmetic call calculate with the user's expression "
    "copied exactly; never work out numbers yourself. Never repeat a tool call that "
    "already succeeded.\nYour task: {task}"
)


VERSION = tracing.prompt_version(SYSTEM_PROMPT)  # tags this agent's spans

__all__ = ["NAME", "productivity_agent", "run_agent", "run_tool", "step_model"]


# Run the loop for the supervisor's latest task.
# Returns {"steps": [...], "summary": str, "stopped": why}.
def run_agent(state: LeoState, chat: Callable, tools: dict[str, Tool],
              max_steps: int, force_cloud: bool = False) -> dict:
    task = (state.get("plan") or [""])[-1]
    prompt = SYSTEM_PROMPT.format(tools=describe_tools(tools), task=task)
    return run_steps(prompt, VERSION, state, chat, tools, max_steps, force_cloud)


# Build the graph node for this agent. Its result goes in agent_results["productivity"].
def productivity_agent(chat: Callable, tools: dict[str, Tool], max_steps: int) -> Callable:
    return agent_node(NAME, lambda state, cloud: run_agent(state, chat, tools,
                                                           max_steps, cloud))
