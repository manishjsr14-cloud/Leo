"""M1.4 real productivity check. Runs 4 fixed turns through the real graph with
the real LLM gateway and the REAL productivity tools on an empty temporary
database (never leo_data/), and writes a new report. Per turn: each agent
step's reply, the stop reason, tool calls and results, LLM calls and time.
It ends with the full tasks table and a PASS/FAIL verdict.

  python -m evals.m1_4_cli_check evals/reports/m1.4_cli_check_<date>.md

Reports run 1 and 2 used the mock tools; from run 3 the real tools on a
throwaway database are used (as agreed for M1.4). No personal data is touched.
Timers are not rung (no schedule function is passed).
"""

import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from evals.m1_4_check_helpers import (
    CountingChat,
    call_label,
    logged,
    recorded,
    task_rows,
    tasks_table,
)
from evals.machine import machine_line
from leo import cli
from leo.agents.productivity import NAME, productivity_agent
from leo.config import load_config
from leo.graph.builder import build_graph
from leo.llm.gateway import LLMUnavailable
from leo.memory.store import open_db
from leo.tools.real.productivity import real_productivity_tools
from leo.tools.registry import by_name

# Fixed before the run: add a task, a percentage, a two-step task, Hinglish.
TURNS = [
    "add milk to my tasks",
    "what is 18% of 2450",
    "complete my milk task",
    "Chai ke liye 10 minute ka timer laga do",
]

# Pass rule v2, committed before report 5. The tools that succeed in each turn
# must be exactly these, in this order; and at the end the tasks table must hold
# exactly one task with "milk" in its title, with done = 1.
# Change log: v1 (report 4) expected ["list_tasks", "complete_task"] in turn 3.
# v2 expects exactly one successful complete_task, because complete_task now
# takes a title (decided after report 4, which stays a FAIL under v1).
EXPECTED_TOOLS = [["add_task"], ["calculate"], ["complete_task"], ["start_timer"]]
PASS_RULE = "v2"


# True when a logged tool call succeeded (its result is not an {"error": ...} dict).
def succeeded(call) -> bool:
    return not (isinstance(call.result, dict) and "error" in call.result)


# Report lines for one turn's details.
def turn_details(number, line, text, calls, stops, tools_run, expected, good, ok) -> list[str]:
    lines = [f"### Turn {number}", "", f"**You:** {line}", "", f"**Leo:** {text}", "",
             "LLM calls, in order: " + ", ".join(call_label(c) for c in calls), "",
             "Agent step replies:"]
    lines += [f"- `{c['text']}`" for c in calls if c["node"] == "agent"] or ["- none"]
    lines += ["", f"Stop reason: {', '.join(stops) or 'agent not run'}", "", "Tool calls:"]
    lines += [f"- `{c.tool}({c.args})` -> `{c.result}`" for c in tools_run] or ["- none"]
    verdict = "PASS" if ok else "FAIL"
    return lines + ["", f"Expected successful tools: {expected}; got: {good} -> {verdict}", ""]


# Run the turns as one conversation on `conn`. Returns report lines and turn verdicts.
def run_turns(max_steps: int, conn) -> tuple[list[str], list[bool]]:
    chat, log, outcomes = CountingChat(), [], []
    tools = by_name([logged(t, log) for t in real_productivity_tools(conn)])
    agent = recorded(productivity_agent(chat, tools, max_steps), NAME, outcomes)
    graph = build_graph(chat, agents={NAME: agent})
    history: list = []
    rows, details, verdicts = [], [], []
    for number, (line, expected) in enumerate(zip(TURNS, EXPECTED_TOOLS), start=1):
        calls_before, log_before, runs_before = len(chat.calls), len(log), len(outcomes)
        start = time.perf_counter()
        try:
            reply, history = cli.run_turn(graph, history, line, False)
            text = reply.content
        except LLMUnavailable as error:  # both models failed: report it
            text = f"FAILED: {error!r}"
        wall = time.perf_counter() - start
        calls, tools_run = chat.calls[calls_before:], log[log_before:]
        stops = [o["stopped"] for o in outcomes[runs_before:]]
        good = [c.tool for c in tools_run if succeeded(c)]
        ok = good == expected
        verdicts.append(ok)
        rows.append(f"| {number} | {len(calls)} | {len(tools_run)} | "
                    f"{', '.join(stops) or 'agent not run'} | {wall:.2f} | "
                    f"{'PASS' if ok else 'FAIL'} |")
        details += turn_details(number, line, text, calls, stops, tools_run, expected, good, ok)
    lines = ["## Turns",
             "turn_s is wall time for the whole graph run (supervisor, agent loop, responder).",
             "", "| turn | llm_calls | tool_calls | stop_reason | turn_s | result |",
             "|---|---|---|---|---|---|", *rows, "", "## Details", "", *details]
    return lines, verdicts


# Check the end state: exactly one task with "milk" in the title, marked done.
def milk_verdict(rows) -> tuple[bool, str]:
    milk = [r for r in rows if "milk" in r["title"].lower()]
    ok = len(milk) == 1 and milk[0]["done"] == 1
    return ok, f"milk tasks: {len(milk)}, done values: {[r['done'] for r in milk]}"


# Write a new report; refuse to overwrite an earlier one.
def main() -> None:
    report = Path(sys.argv[1])
    if report.exists():
        sys.exit(f"{report} already exists; earlier reports are never rewritten.")
    config = load_config()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
        conn = open_db(Path(folder) / "leo.db")
        lines, verdicts = run_turns(config.agent.max_steps, conn)
        rows = task_rows(conn)
        conn.close()
    milk_ok, milk_text = milk_verdict(rows)
    passed = all(verdicts) and milk_ok
    header = [f"# M1.4 productivity check — {stamp}", machine_line(),
              (f"Local model: {config.llm.primary.model}. "
               f"Fallback: {config.llm.fallback.model}. max_hops: {config.graph.max_hops}. "
               f"agent.max_steps: {config.agent.max_steps}. "
               "Agent: productivity on real tools, empty temporary database."), "",
              (f"**Overall: {'PASS' if passed else 'FAIL'}** (turns passed: "
              f"{sum(verdicts)}/{len(verdicts)}; end state {'PASS' if milk_ok else 'FAIL'}: "
              f"{milk_text})"), "",
              (f"Pass rule {PASS_RULE}: each turn's successful tool calls equal the expected "
               "list exactly; "
              "the tasks table ends with exactly one milk task, done = 1."), ""]
    footer = ["## Tasks table at the end", "The database was empty before turn 1.", "",
              *tasks_table(rows)]
    report.write_text("\n".join(header + lines + footer) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # replies may contain emoji
    print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
