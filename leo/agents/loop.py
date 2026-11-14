"""The step loop shared by every specialist agent (section 4.2, decision M1.4).

A small loop on the gateway's schema-checked JSON actions (not create_react_agent).
Each LLM reply is either
  {"tool": "<name>", "args": {...}}   -> run that tool, show the model the result
  {"done": true, "summary": "..."}    -> finished, hand back to the supervisor
The first reply must be a tool call: "done" is offered only after a tool ran.
The loop stops after max_steps LLM replies. Tool errors are shown to the
model so it can try again; they never crash the graph. 🔴 tools are always
refused here (call_tool without approved=True); approval arrives in M2.5.
Each agent passes in its own system prompt and prompt version.
"""

import json
from collections.abc import Callable
from typing import Any, Literal, Union

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, RootModel, ValidationError, create_model

from leo.graph.builder import cloud_requested
from leo.graph.state import LeoState, chat_messages
from leo.ops import tracing
from leo.tools.base import Tool, ToolError, plain
from leo.tools.registry import ApprovalRequiredError, UnknownToolError, call_tool


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


# The loop itself, with `prompt` already filled in (tools, task, ...).
# Returns {"steps": [...], "summary": str, "stopped": why}.
def run_steps(prompt: str, version: str, state: LeoState, chat: Callable,
              tools: dict[str, Tool], max_steps: int, force_cloud: bool = False) -> dict:
    messages = chat_messages(prompt, state)
    first_step, later_steps = step_model(tools, first_step=True), step_model(tools)
    steps: list[dict] = []
    # Each step is one span: its LLM call and tool call are nested inside it.
    for number in range(1, max_steps + 1):
        tags = {"step": number, "prompt_version": version}
        with tracing.span(f"step {number}", "span", metadata=tags) as span:
            result = chat(messages, first_step if number == 1 else later_steps, force_cloud)
            if not result.valid:
                span.update(metadata={**tags, "action": "invalid_output"})
                return {"steps": steps, "summary": "", "stopped": "invalid_output"}
            action = result.parsed.root
            if isinstance(action, Done):
                span.update(metadata={**tags, "action": "done"})
                return {"steps": steps, "summary": action.summary, "stopped": "done"}
            # Unset optional arguments (None) are left out, e.g. title when task_id is given.
            args = plain(action.args)
            output = run_tool(tools, action.tool, args)
            failed = isinstance(output, dict) and "error" in output
            span.update(metadata={**tags, "action": action.tool, "tool_ok": not failed})
        steps.append({"tool": action.tool, "args": args, "result": output})
        messages += [
            {"role": "assistant", "content": result.text},
            {"role": "user", "content": f"Result of {action.tool}: {json.dumps(output)}"},
        ]
    return {"steps": steps, "summary": "", "stopped": "max_steps"}


# Build a graph node from `run(state, force_cloud)`. Its result goes in
# agent_results[name]; after done the agent is also added to completed_agents,
# so the supervisor does not choose it again for the same request (section 4.3).
def agent_node(name: str, run: Callable[[LeoState, bool], dict]) -> Callable:
    # The node LangGraph calls; the run config says whether to force Groq.
    def node(state: LeoState, config: RunnableConfig) -> dict:
        outcome = run(state, cloud_requested(config))
        update = {"agent_results": {**(state.get("agent_results") or {}), name: outcome}}
        if outcome["stopped"] == "done":
            update["completed_agents"] = [*(state.get("completed_agents") or []), name]
        return update

    return node
