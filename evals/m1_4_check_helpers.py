"""Helpers for evals/m1_4_cli_check.py: count LLM calls, log real tool calls,
record each agent run's outcome, and print the tasks table.
"""

import sqlite3

from leo.graph.supervisor import SupervisorDecision
from leo.llm import gateway
from leo.tools.base import Tool, ToolCall, ToolError


class CountingChat:
    """Wraps gateway.chat and records each call: node, provider and reply text."""

    def __init__(self):
        self.calls: list[dict] = []

    # Call the real gateway and record who called it, who answered and what came back.
    def __call__(self, messages, output_model=None, force_cloud=False):
        result = gateway.chat(messages, output_model, force_cloud)
        if isinstance(output_model, type) and issubclass(output_model, SupervisorDecision):
            node = "supervisor"
        elif output_model is None:
            node = "responder"
        else:
            node = "agent"
        self.calls.append({"node": node, "provider": result.provider,
                           "fallback": result.fallback_reason, "text": result.text})
        return result


# Short label for one LLM call, e.g. "agent:ollama" or "agent:groq (timeout)".
def call_label(call: dict) -> str:
    reason = f" ({call['fallback']})" if call["fallback"] else ""
    return f"{call['node']}:{call['provider']}{reason}"


# Wrap a real tool so every call (and any ToolError) is added to `log`.
def logged(tool: Tool, log: list[ToolCall]) -> Tool:
    # Run the real function and record the call.
    def run(args):
        try:
            result = tool.fn(args)
        except ToolError as error:
            result = {"error": str(error)}
            log.append(ToolCall(tool=tool.name, args=args.model_dump(mode="json"), result=result))
            raise
        log.append(ToolCall(tool=tool.name, args=args.model_dump(mode="json"), result=result))
        return result
    return tool.model_copy(update={"fn": run})


# Wrap an agent node so each run's outcome (steps, stop reason) is kept in `outcomes`.
def recorded(node, name: str, outcomes: list[dict]):
    # Run the agent and keep a copy of what it returned.
    def run(state, config):
        update = node(state, config)
        outcomes.append(update["agent_results"][name])
        return update
    return run


# All rows of the tasks table, oldest first.
def task_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(conn.execute(
        "SELECT id, title, done, created_at, done_at FROM tasks ORDER BY id"))


# The tasks table as markdown lines.
def tasks_table(rows: list[sqlite3.Row]) -> list[str]:
    lines = ["| id | title | done | created_at | done_at |", "|---|---|---|---|---|"]
    lines += [f"| {r['id']} | {r['title']} | {r['done']} | {r['created_at']} | {r['done_at']} |"
              for r in rows]
    return lines
