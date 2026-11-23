"""The step loop shared by every specialist agent (section 4.2, decision M1.4).

A small loop on the gateway's schema-checked JSON actions (not create_react_agent).
Each LLM reply (shape in leo/agents/step_schema.py) is either
  {"<tool name>": {...args}}          -> run that tool, show the model the result
  {"done": {"summary": "..."}}        -> finished, hand back to the supervisor
The first reply must be a tool call: "done" is offered only after a tool ran.
The loop stops after max_steps LLM replies, or when the model repeats a tool
call (same tool, same arguments) that already succeeded, or was refused for
approval, in this run: the repeat is not run and the run ends ("repeated_call").
A tool may let code fill in its arguments (Tool.fill); the step then records
the full arguments that were sent to the tool. Tool errors are shown to the
model so it can try again; they never crash the graph. 🔴 tools are always
refused here (call_tool without approved=True) and the step is marked
needs_approval; approval arrives in M2.5. A tool that raises AskUser ends the
run ("ask"), with the code's question as the summary.
Each agent passes in its own system prompt and prompt version.
An agent may also pass a finish rule (leo/agents/finish.py, M1.8): when it
says so after a step that succeeded or was refused for approval, the run ends
("done") with a summary written by code, without another LLM call.
"""

import json
from collections.abc import Callable
from typing import Any

from langchain_core.runnables import RunnableConfig
from pydantic import ValidationError

from leo.agents.finish import Finish
from leo.agents.step_schema import loose_call, read_action, step_model
from leo.graph.builder import cloud_requested
from leo.graph.result_words import result_in_words
from leo.graph.state import LeoState, chat_messages
from leo.ops import tracing
from leo.tools.base import AskUser, Tool, ToolError, plain
from leo.tools.registry import ApprovalRequiredError, UnknownToolError, call_tool


# One line per tool for the prompt: name, description and its arguments.
def describe_tools(tools: dict[str, Tool]) -> str:
    lines = []
    for tool in tools.values():
        props = (tool.model_args or tool.args_model).model_json_schema().get("properties", {})
        args = ", ".join(f"{k}: {v.get('type', 'any')}" for k, v in props.items())
        lines.append(f"- {tool.name}({args}): {tool.description}")
    return "\n".join(lines)


# Run one tool; on a bad call return {"error": ...} for the model instead of raising.
# A refused 🔴 call also carries needs_approval; an AskUser carries the question.
def run_tool(tools: dict[str, Tool], name: str, args: dict) -> Any:
    try:
        return call_tool(tools, name, args)
    except AskUser as error:
        return {"error": "the user must answer first", "ask": str(error)}
    except ApprovalRequiredError as error:
        return {"error": str(error), "needs_approval": True}
    except ValidationError as error:
        problems = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}"
                             for e in error.errors())
        return {"error": f"bad arguments: {problems}"}
    except (ToolError, UnknownToolError) as error:
        return {"error": str(error)}


# The full arguments for a call: the model's own, or the tool's fill of them.
# Returns (args, None), or (the model's args, an error output) when filling refuses.
def full_args(tools: dict[str, Tool], name: str, args: dict) -> tuple[dict, dict | None]:
    tool = tools.get(name)
    if tool is None or tool.fill is None:
        return args, None
    try:
        return tool.fill(args), None
    except AskUser as error:
        return args, {"error": "the user must answer first", "ask": str(error)}
    except ToolError as error:
        return args, {"error": str(error)}


# One step run by code, not the model (M1 exit check): the tool runs with
# code-filled arguments and is recorded like a model step.
def code_step(tools: dict[str, Tool], name: str, args: dict) -> dict:
    full, refused = full_args(tools, name, args)
    return {"tool": name, "args": full, "result": refused or run_tool(tools, name, full)}


# One string per call, the same for the same tool and arguments in any key order.
def call_key(tool: str, args: dict) -> str:
    return json.dumps([tool, args], sort_keys=True)


# The loop itself, with `prompt` already filled in (tools, task, ...).
# A reply that fails the schema but still names one known tool (e.g. an end
# before its start) is run once through call_tool, so the model sees the
# argument error like any tool error; a second such reply ends the run.
# Returns {"steps": [...], "summary": str, "stopped": why}.
def run_steps(prompt: str, version: str, state: LeoState, chat: Callable,
              tools: dict[str, Tool], max_steps: int, force_cloud: bool = False,
              finish: Finish | None = None) -> dict:
    messages = chat_messages(prompt, state)
    first_step, later_steps = step_model(tools, first_step=True), step_model(tools)
    steps: list[dict] = []
    done_calls: set[str] = set()  # successful calls so far, as call_key strings
    bad_args_shown = False        # an argument error was already sent back once
    # Each step is one span: its LLM call and tool call are nested inside it.
    for number in range(1, max_steps + 1):
        tags = {"step": number, "prompt_version": version}
        with tracing.span(f"step {number}", "span", metadata=tags) as span:
            result = chat(messages, first_step if number == 1 else later_steps, force_cloud)
            if result.valid:
                name, value = read_action(result.parsed.root)
                if name == "done":
                    span.update(metadata={**tags, "action": "done"})
                    return {"steps": steps, "summary": value.summary, "stopped": "done"}
                # Unset optional arguments (None) are left out, e.g. title when task_id is given.
                args = plain(value)
            else:
                loose = None if bad_args_shown else loose_call(result.text, tools)
                if loose is None:
                    span.update(metadata={**tags, "action": "invalid_output"})
                    return {"steps": steps, "summary": "", "stopped": "invalid_output"}
                (name, args), bad_args_shown = loose, True
            args, refused = full_args(tools, name, args)  # code-filled args, if any
            if call_key(name, args) in done_calls:
                span.update(metadata={**tags, "action": "repeated_call"})
                return {"steps": steps, "summary": "", "stopped": "repeated_call"}
            output = refused or run_tool(tools, name, args)
            failed = isinstance(output, dict) and "error" in output
            span.update(metadata={**tags, "action": name, "tool_ok": not failed})
            if not failed or output.get("needs_approval") is True:
                done_calls.add(call_key(name, args))  # also no retry of a refused 🔴 call
        steps.append({"tool": name, "args": args, "result": output})
        if isinstance(output, dict) and "ask" in output:
            return {"steps": steps, "summary": output["ask"], "stopped": "ask"}
        ok = not failed or output.get("needs_approval") is True
        if ok and finish is not None and finish(name):  # done in code, no LLM call
            return {"steps": steps, "summary": result_in_words(name, output) or "",
                    "stopped": "done"}
        messages += [
            {"role": "assistant", "content": result.text},
            {"role": "user", "content": f"Result of {name}: {json.dumps(output)}"},
        ]
    return {"steps": steps, "summary": "", "stopped": "max_steps"}


# Build a graph node from `run(state, force_cloud)`. Its result goes in
# agent_results[name]; after done the agent is also added to completed_agents.
def agent_node(name: str, run: Callable[[LeoState, bool], dict]) -> Callable:
    # The node LangGraph calls; the run config says whether to force Groq.
    def node(state: LeoState, config: RunnableConfig) -> dict:
        outcome = run(state, cloud_requested(config))
        update = {"agent_results": {**(state.get("agent_results") or {}), name: outcome}}
        if outcome["stopped"] == "done":
            update["completed_agents"] = [*(state.get("completed_agents") or []), name]
        return update

    return node
