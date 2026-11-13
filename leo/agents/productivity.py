"""The productivity agent: tasks, notes, timers and the calculator (section 4.2).

A small loop on the gateway's schema-checked JSON actions (not create_react_agent,
see section 4.2). Each LLM reply is either
  {"tool": "<name>", "args": {...}}   -> run that tool, show the model the result
  {"done": true, "summary": "..."}    -> finished, hand back to the supervisor
The loop stops after agent.max_steps LLM replies. Tool errors are shown to the
model so it can try again; they never crash the graph. 🔴 tools are always
refused here (call_tool without approved=True); approval arrives in M2.5.
"""

import json
from collections.abc import Callable
from typing import Any, Literal

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, ValidationError, create_model, model_validator

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
    "finished.\nRules: to complete a task named by the user, call list_tasks first "
    "to find its id. For any arithmetic call calculate with the user's expression "
    "copied exactly; never work out numbers yourself. Never repeat a tool call that "
    "already succeeded.\nYour task: {task}"
)


class AgentStep(BaseModel):
    """One LLM reply in the loop: a tool call, or done with a summary."""

    tool: str | None = None
    args: dict[str, Any] = {}
    done: bool = False
    summary: str = ""

    # A reply must either name a tool or say it is done.
    @model_validator(mode="after")
    def tool_or_done(self):
        if not self.done and self.tool is None:
            raise ValueError("give a tool, or done: true")
        return self


# The step schema for these tools: `tool` may only be one of their names,
# so Ollama's structured output cannot invent a tool.
def step_model(tools: dict[str, Tool]) -> type[AgentStep]:
    names = Literal[tuple(tools)]  # type: ignore[valid-type]
    return create_model("AgentStep", __base__=AgentStep, tool=(names | None, None))


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
    schema = step_model(tools)
    steps: list[dict] = []
    for _ in range(max_steps):
        result = chat(messages, schema, force_cloud)
        if not result.valid:
            return {"steps": steps, "summary": "", "stopped": "invalid_output"}
        action = result.parsed
        if action.done:
            return {"steps": steps, "summary": action.summary, "stopped": "done"}
        output = run_tool(tools, action.tool, action.args)
        steps.append({"tool": action.tool, "args": action.args, "result": output})
        messages += [
            {"role": "assistant", "content": result.text},
            {"role": "user", "content": f"Result of {action.tool}: {json.dumps(output)}"},
        ]
    return {"steps": steps, "summary": "", "stopped": "max_steps"}


# Build the graph node for this agent. Its result goes in agent_results["productivity"].
def productivity_agent(chat: Callable, tools: dict[str, Tool], max_steps: int) -> Callable:
    # The node LangGraph calls; the run config says whether to force Groq.
    def node(state: LeoState, config: RunnableConfig) -> dict:
        outcome = run_agent(state, chat, tools, max_steps, cloud_requested(config))
        return {"agent_results": {**(state.get("agent_results") or {}), NAME: outcome}}

    return node
