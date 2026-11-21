"""M1.5 real research check. Runs 4 fixed turns as one conversation through the
real graph with the real LLM gateway, the REAL research tools (internet:
Open-Meteo, DuckDuckGo, web pages; agreed for M1.5) and the real productivity
tools on an empty temporary database (never leo_data/). Writes a new report
with, per turn: the supervisor plan, the agents run, agent step replies, tool calls
and results, LLM calls and time, and the verdict.

  python -m evals.m1_5_cli_check evals/reports/m1.5_cli_check_<date>.md

No personal data is sent: only the fixed turns below.
"""

import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from evals.m1_4_check_helpers import CountingChat, logged
from evals.m1_5_check_helpers import chosen, tagged, turn_details
from evals.m1_5_pass_rules import RULES, cell, verdict_v1, verdict_v2
from evals.machine import machine_line
from leo import cli
from leo.agents.productivity import productivity_agent
from leo.agents.research import research_agent
from leo.config import load_config
from leo.graph.builder import build_graph
from leo.llm.gateway import LLMUnavailable
from leo.memory.store import open_db
from leo.tools.real.productivity import real_productivity_tools
from leo.tools.real.research import real_research_tools
from leo.tools.registry import by_name

# Fixed before the run.
TURNS = [
    "Will it rain in Pune tomorrow?",
    "Kal Pune mein baarish hogi?",
    "Search the web for the opening hours of Shaniwar Wada",
    "add milk to my tasks",
]

HEADER = ("| turn | supervisor_plan | agents_run | llm_calls | tool_calls | turn_s "
          "| v1 | v2 |")


# Run the turns as one conversation. Returns report lines and the scored verdicts.
def run_turns(config, conn) -> tuple[list[str], dict[str, list[bool]]]:
    chat, log, runs = CountingChat(), [], []
    steps = config.agent.max_steps
    tasks = by_name([logged(t, log) for t in real_productivity_tools(conn)])
    web = by_name([logged(t, log) for t in real_research_tools(config.research)])
    agents = {"productivity": tagged(productivity_agent(chat, tasks, steps), "productivity", runs),
              "research": tagged(research_agent(chat, web, steps), "research", runs)}
    graph = build_graph(chat, agents=agents, config=config)
    history: list = []
    rows, details, verdicts = [], [], {"v1": [], "v2": []}
    for number, line in enumerate(TURNS, start=1):
        calls_before, log_before, runs_before = len(chat.calls), len(log), len(runs)
        start = time.perf_counter()
        try:
            reply, history = cli.run_turn(graph, history, line, False)
            text = reply.content
        except LLMUnavailable as error:  # both models failed: report it
            text = f"FAILED: {error!r}"
        wall = time.perf_counter() - start
        calls, tools_run, new = chat.calls[calls_before:], log[log_before:], runs[runs_before:]
        ran = [name for name, _ in new]
        stops = [f"{name}: {outcome['stopped']}" for name, outcome in new]
        plans = chosen(calls)
        ok = {"v1": verdict_v1(number, ran, tools_run, text),
              "v2": verdict_v2(number, ran, tools_run, text)}
        for rule, value in ok.items():
            if value is not None:
                verdicts[rule].append(value)
        result = f"v1 {cell(ok['v1'])}, v2 {cell(ok['v2'])}"
        rows.append(f"| {number} | {plans} | {', '.join(ran) or 'none'} | {len(calls)} | "
                    f"{len(tools_run)} | {wall:.2f} | {cell(ok['v1'])} | {cell(ok['v2'])} |")
        details += turn_details(number, line, text, calls, plans, ran, stops, tools_run,
                                result)
    lines = ["## Turns",
             "turn_s is wall time for the whole graph run (supervisor, agents, responder).",
             "", HEADER, "|---|---|---|---|---|---|---|---|", *rows, "", "## Details", "",
             *details]
    return lines, verdicts


# Write a new report; refuse to overwrite an earlier one.
def main() -> None:
    report = Path(sys.argv[1])
    if report.exists():
        sys.exit(f"{report} already exists; earlier reports are never rewritten.")
    config = load_config()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
        conn = open_db(Path(folder) / "leo.db")
        lines, verdicts = run_turns(config, conn)
        conn.close()
    overall = {rule: "PASS" if len(verdicts[rule]) == len(turns) and all(verdicts[rule])
               else "FAIL" for rule, turns in RULES.items()}
    header = [f"# M1.5 research check — {stamp}", machine_line(),
              (f"Local model: {config.llm.primary.model}. "
               f"Fallback: {config.llm.fallback.model}. max_hops: {config.graph.max_hops}. "
               f"agent.max_steps: {config.agent.max_steps}. Agents: productivity (real "
               "tools, empty temporary database) and research (real tools, internet)."), "",
              *[f"**Overall {rule}: {overall[rule]}** (scored turns passed: "
                f"{sum(verdicts[rule])}/{len(turns)})" for rule, turns in RULES.items()], "",
              ("Pass rule v1: turn 1 runs the research agent, get_weather succeeds with a "
               "place containing 'pune', and the reply contains 'open-meteo'; turn 4 runs "
               "the productivity agent and never the research agent."),
              ("Pass rule v2 (added after report 1, before this run): v1, plus turn 1's "
               "get_weather result has a row labelled 'tomorrow', and turn 3 (web question) "
               "does not run productivity. Turn 2 is recorded only under both rules."), ""]
    report.write_text("\n".join(header + lines) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # replies may contain emoji
    print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
