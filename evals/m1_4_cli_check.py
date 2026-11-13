"""M1.4 real productivity check. Runs 4 fixed turns through the real graph with
the real LLM gateway and the REAL productivity tools on an empty temporary
database (never leo_data/), and writes a new report: tool calls, LLM calls
(by node, with provider), wall time per turn, and the full tasks table at the end.

  python -m evals.m1_4_cli_check evals/reports/m1.4_cli_check_<date>.md

Reports run 1 and 2 used the mock tools; from run 3 the real tools on a
throwaway database are used (as agreed for M1.4). No personal data is touched.
Timers are not rung (no schedule function is passed).
"""

import sqlite3
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from leo import cli
from leo.agents.productivity import productivity_agent
from leo.config import load_config
from leo.graph.builder import build_graph
from leo.graph.supervisor import SupervisorDecision
from leo.llm import gateway
from leo.llm.gateway import LLMUnavailable
from leo.memory.store import open_db
from leo.tools.base import Tool, ToolCall, ToolError
from leo.tools.real.productivity import real_productivity_tools
from leo.tools.registry import by_name

# Fixed before the run: add a task, a percentage, a two-step task, Hinglish.
TURNS = [
    "add milk to my tasks",
    "what is 18% of 2450",
    "complete my milk task",
    "Chai ke liye 10 minute ka timer laga do",
]


class CountingChat:
    """Wraps gateway.chat and records which node called it and who answered."""

    def __init__(self):
        self.calls: list[str] = []

    # Call the real gateway and note "<node>:<provider>" for this call.
    def __call__(self, messages, output_model=None, force_cloud=False):
        result = gateway.chat(messages, output_model, force_cloud)
        if isinstance(output_model, type) and issubclass(output_model, SupervisorDecision):
            node = "supervisor"
        elif output_model is None:
            node = "responder"
        else:
            node = "agent"
        reason = f" ({result.fallback_reason})" if result.fallback_reason else ""
        self.calls.append(f"{node}:{result.provider}{reason}")
        return result


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


# The whole tasks table as markdown rows.
def tasks_table(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT id, title, done, created_at, done_at FROM tasks ORDER BY id")
    lines = ["| id | title | done | created_at | done_at |", "|---|---|---|---|---|"]
    lines += [f"| {r['id']} | {r['title']} | {r['done']} | {r['created_at']} | {r['done_at']} |"
              for r in rows]
    return lines


# Run the turns as one conversation on `conn` and return the report lines.
def run_turns(max_steps: int, conn: sqlite3.Connection) -> list[str]:
    chat, log = CountingChat(), []
    tools = by_name([logged(t, log) for t in real_productivity_tools(conn)])
    agent = productivity_agent(chat, tools, max_steps)
    graph = build_graph(chat, agents={"productivity": agent})
    history: list = []
    rows, details = [], []
    for number, line in enumerate(TURNS, start=1):
        calls_before, log_before = len(chat.calls), len(log)
        start = time.perf_counter()
        try:
            reply, history = cli.run_turn(graph, history, line, False)
            text = reply.content
        except LLMUnavailable as error:  # both models failed: report it
            text = f"FAILED: {error!r}"
        wall = time.perf_counter() - start
        calls = chat.calls[calls_before:]
        tools = log[log_before:]
        rows.append(f"| {number} | {len(calls)} | {len(tools)} | {wall:.2f} |")
        details += [f"### Turn {number}", "", f"**You:** {line}", "",
                    f"**Leo:** {text}", "", "LLM calls, in order: " + ", ".join(calls), "",
                    "Tool calls:"]
        details += [f"- `{c.tool}({c.args})` -> `{c.result}`" for c in tools] or ["- none"]
        details.append("")
    return [
        "## Turns",
        "turn_s is wall time for the whole graph run (supervisor, agent loop, responder).",
        "",
        "| turn | llm_calls | tool_calls | turn_s |",
        "|---|---|---|---|",
        *rows,
        "",
        "## Details",
        "",
        *details,
        "## Tasks table at the end",
        "The database was empty before turn 1.",
        "",
        *tasks_table(conn),
    ]


# Write a new report; refuse to overwrite an earlier one.
def main() -> None:
    report = Path(sys.argv[1])
    if report.exists():
        sys.exit(f"{report} already exists; earlier reports are never rewritten.")
    config = load_config()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = [f"# M1.4 productivity check — {stamp}",
              (f"Local model: {config.llm.primary.model}. "
               f"Fallback: {config.llm.fallback.model}. max_hops: {config.graph.max_hops}. "
               f"agent.max_steps: {config.agent.max_steps}. "
               "Agent: productivity on real tools, empty temporary database."),
              ""]
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
        conn = open_db(Path(folder) / "leo.db")
        lines = run_turns(config.agent.max_steps, conn)
        conn.close()
    report.write_text("\n".join(header + lines) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # replies may contain emoji
    print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
