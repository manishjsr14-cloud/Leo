"""The productivity agent: tasks, notes, timers and the calculator (section 4.2).

Runs the shared step loop (leo/agents/loop.py) with its prompt from
prompts/productivity.yaml. Choosing the right agent is the supervisor's job.
After one successful write the run ends in code, unless the message links
more requests (leo/agents/finish.py, M1.8). Reads (list_tasks, list_notes)
never end a run early: a list may be the first step of a change.
M1 exit check (K05): an "X% of Y" question with nothing else asked is
calculated by code (leo/agents/percent.py builds the expression), with no
LLM call; the code reply then answers.
"""

from collections.abc import Callable

from leo.agents.calculate_guard import guard_calculate
from leo.agents.finish import finish_rule
from leo.agents.loop import (
    agent_node,
    code_step,
    describe_tools,
    run_steps,
    run_tool,
    step_model,
)
from leo.agents.percent import percent_expression
from leo.graph.result_words import result_in_words
from leo.graph.state import LeoState, latest_user_text
from leo.language.normalize import has_joiner
from leo.llm.prompts import load_prompt
from leo.tools.base import Tool

NAME = "productivity"
PROMPT = load_prompt("productivity")  # prompts/productivity.yaml
VERSION = PROMPT.tag                  # tags this agent's spans
ENDS_RUN = {"add_task", "complete_task", "add_note", "start_timer", "calculate"}

__all__ = ["NAME", "productivity_agent", "run_agent", "run_tool", "step_model"]


# Run the loop for the supervisor's latest task.
# Returns {"steps": [...], "summary": str, "stopped": why}.
def run_agent(state: LeoState, chat: Callable, tools: dict[str, Tool],
              max_steps: int, force_cloud: bool = False) -> dict:
    task, text = (state.get("plan") or [""])[-1], latest_user_text(state)
    tools = guard_calculate(tools, text)  # numbers must come from the message (M1.8)
    expression = percent_expression(text)
    if expression is not None and "calculate" in tools and not has_joiner(text):
        step = code_step(tools, "calculate", {"expression": expression})
        if "error" not in step["result"]:  # done by code; else the model tries as before
            return {"steps": [step], "stopped": "done",
                    "summary": result_in_words("calculate", step["result"]) or ""}
    prompt = PROMPT.render(tools=describe_tools(tools), task=task)
    finish = finish_rule(text, ENDS_RUN)
    return run_steps(prompt, VERSION, state, chat, tools, max_steps, force_cloud, finish)


# Build the graph node for this agent. Its result goes in agent_results["productivity"].
def productivity_agent(chat: Callable, tools: dict[str, Tool], max_steps: int) -> Callable:
    return agent_node(NAME, lambda state, cloud: run_agent(state, chat, tools,
                                                           max_steps, cloud))
