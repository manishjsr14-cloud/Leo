"""The productivity agent: tasks, notes, timers and the calculator (section 4.2).

A small loop on the gateway's schema-checked JSON actions (not create_react_agent,
see section 4.2). Each LLM reply is either
  {"tool": "<name>", "args": {...}}   -> run that tool, show the model the result
  {"done": true, "summary": "..."}    -> finished, hand back to the supervisor
The first reply must be a tool call: "done" is offered only after a tool ran.
Choosing the right agent (or FINISH) is the supervisor's job.
An agent that returns done is added to completed_agents, so the
supervisor does not choose it again for the same request (section 4.3).
The loop stops after agent.max_steps LLM replies. Tool errors are shown to the
model so it can try again; they never crash the graph. 🔴 tools are always
refused here (call_tool without approved=True); approval arrives in M2.5.
"""

import json
from collections.abc import Callable
from typing import Any, Literal, Union

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, RootModel, ValidationError, create_model

from leo.graph.builder import cloud_requested
from leo.graph.state import LeoState, chat_messages
from leo.tools.base import Tool, ToolError
from leo.tools.registry import ApprovalRequiredError, UnknownToolError, call_tool

NAME = "productivity"

# Kept here until versioned prompt files arrive in M1.8.
SYSTEM_PROMPT = (
    "You are Leo's productivity agent. You manage the user's to-do tasks and "
    "notes, start timers and do arithmetic, only through these tools:\n{tools}\n"
    'Reply only with JSON: either {{"tool": "<name>", "args": {{...}}}} to use one '
    'tool, or {{"done": true, "summary": "<what you did and the results>"}} when '
    "finished.\n"
    'Rules: a task title is just the item, e.g. "milk" for "add milk to my tasks". '
    "To complete a task named by the user, always call list_tasks first to find its "
    "id, then complete_task. For any arithmetic call calculate with the user's expression "
    "copied exactly; never work out numbers yourself. Never repeat a tool call that "
    "already succeeded.\nYour task: {task}"
)


class Done(BaseModel):
    """The reply that ends the loop, with a short summary for the responder."""

    done: Literal[True]
    summary: str


# The step schema for these tools: one option per tool, each with that tool's
# own required, typed arguments. Ollama's structured output then cannot invent a
# tool or leave out its arguments (an open "args" object let the model reply
# {"tool": "add_task"} with no args; see the first M1.4 report).
# The first step leaves Done out: the model said "done" without calling any
# tool, so it must act first. (A "cannot" option was tried and dropped: the
# model declined requests it could do; see the third M1.4 report.)
def step_model(tools: dict[str, Tool], first_step: bool = False) -> type[RootModel]:
    options: list[type[BaseModel]] = [
        create_model(f"Call_{name}", tool=(Literal[name], ...), args=(tool.args_model, ...))
        for name, tool in tools.items()
    ]
    if not first_step:
        options.append(Done)
    return RootModel[Union[tuple(options)]]  # noqa: UP007


# One line per tool for the prompt: name, description and its arguments.
def describe_tools(tools: dict[str, Tool]) -> str:
    lines = []
    for tool in tools.values():
        props = tool.args_model.model_json_schema().get("properties", {})
        args = ", ".join(f"{k}: {v.get('type', 'any')}" for k, v in props.items())
        lines.append(f"- {tool.name}({args}): {tool.description}")
    return "\n".join(lines)


# Run one tool; on a bad call return {"error": ...} for the model instead of raising.
def run_tool(tools: dict[str, Tool], name: str, args: dict) -> Any:
    try:
        return call_tool(tools, name, args)
    except ValidationError as error:
        problems = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}"
                             for e in error.errors())
        return {"error": f"bad arguments: {problems}"}
    except (ToolError, UnknownToolError, ApprovalRequiredError) as error:
        return {"error": str(error)}


# The loop itself. Returns {"steps": [...], "summary": str, "stopped": why}.
def run_agent(state: LeoState, chat: Callable, tools: dict[str, Tool],
              max_steps: int, force_cloud: bool = False) -> dict:
    task = (state.get("plan") or [""])[-1]
    prompt = SYSTEM_PROMPT.format(tools=describe_tools(tools), task=task)
    messages = chat_messages(prompt, state)
    first_step, later_steps = step_model(tools, first_step=True), step_model(tools)
    steps: list[dict] = []
    for number in range(max_steps):
        schema = first_step if number == 0 else later_steps
        result = chat(messages, schema, force_cloud)
        if not result.valid:
            return {"steps": steps, "summary": "", "stopped": "invalid_output"}
        action = result.parsed.root
        if isinstance(action, Done):
            return {"steps": steps, "summary": action.summary, "stopped": "done"}
        args = action.args.model_dump(mode="json")
        output = run_tool(tools, action.tool, args)
        steps.append({"tool": action.tool, "args": args, "result": output})
        messages += [
            {"role": "assistant", "content": result.text},
            {"role": "user", "content": f"Result of {action.tool}: {json.dumps(output)}"},
        ]
    return {"steps": steps, "summary": "", "stopped": "max_steps"}


# Build the graph node for this agent. Its result goes in agent_results["productivity"];
# after done it is also added to completed_agents for this request.
def productivity_agent(chat: Callable, tools: dict[str, Tool], max_steps: int) -> Callable:
    # The node LangGraph calls; the run config says whether to force Groq.
    def node(state: LeoState, config: RunnableConfig) -> dict:
        outcome = run_agent(state, chat, tools, max_steps, cloud_requested(config))
        update = {"agent_results": {**(state.get("agent_results") or {}), NAME: outcome}}
        if outcome["stopped"] == "done":
            update["completed_agents"] = [*(state.get("completed_agents") or []), NAME]
        return update

    return node
