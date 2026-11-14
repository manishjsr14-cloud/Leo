"""M1.5 real research check. Runs 4 fixed turns as one conversation through the
real graph with the real LLM gateway, the REAL research tools (internet:
Open-Meteo, DuckDuckGo, web pages; agreed for M1.5) and the real productivity
tools on an empty temporary database (never leo_data/). Writes a new report
with, per turn: the agents the supervisor chose, agent step replies, tool calls
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

# Pass rule v1, committed before the first run. Only turns 1 and 4 are scored;
# turns 2 (Hinglish) and 3 (web search) are recorded only.
# Turn 1: the research agent ran; get_weather succeeded with a place containing
#   "pune" (any case); the reply contains "open-meteo" (any case, which also
#   covers the URL open-meteo.com).
# Turn 4: the productivity agent ran, and the research agent did not run.
PASS_RULE = "v1"
SCORED = {1, 4}
HEADER = "| turn | supervisor_chose | agents_run | llm_calls | tool_calls | turn_s | result |"


# True when a logged tool call succeeded (its result is not an {"error": ...} dict).
def succeeded(call) -> bool:
    return not (isinstance(call.result, dict) and "error" in call.result)


# The verdict for one turn (None for a recorded-only turn).
def verdict(number: int, ran: list[str], tools_run, reply: str) -> bool | None:
    if number == 1:
        weather_ok = any(c.tool == "get_weather" and succeeded(c)
                         and "pune" in c.args.get("place", "").lower() for c in tools_run)
        return "research" in ran and weather_ok and "open-meteo" in reply.lower()
    if number == 4:
        return "productivity" in ran and "research" not in ran
    return None


# Run the turns as one conversation. Returns report lines and the scored verdicts.
def run_turns(config, conn) -> tuple[list[str], list[bool]]:
    chat, log, runs = CountingChat(), [], []
    steps = config.agent.max_steps
    tasks = by_name([logged(t, log) for t in real_productivity_tools(conn)])
    web = by_name([logged(t, log) for t in real_research_tools(config.research)])
    agents = {"productivity": tagged(productivity_agent(chat, tasks, steps), "productivity", runs),
              "research": tagged(research_agent(chat, web, steps), "research", runs)}
    graph = build_graph(chat, agents=agents, config=config)
    history: list = []
    rows, details, verdicts = [], [], []
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
        picks = chosen(calls)
        ok = verdict(number, ran, tools_run, text)
        if ok is not None:
            verdicts.append(ok)
        result = "recorded only" if ok is None else ("PASS" if ok else "FAIL")
        rows.append(f"| {number} | {', '.join(picks)} | {', '.join(ran) or 'none'} | "
                    f"{len(calls)} | {len(tools_run)} | {wall:.2f} | {result} |")
        details += turn_details(number, line, text, calls, picks, ran, stops, tools_run, ok)
    lines = ["## Turns",
             "turn_s is wall time for the whole graph run (supervisor, agents, responder).",
             "", HEADER, "|---|---|---|---|---|---|---|", *rows, "", "## Details", "",
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
    passed = len(verdicts) == len(SCORED) and all(verdicts)
    header = [f"# M1.5 research check — {stamp}",
              (f"Local model: {config.llm.primary.model}. "
               f"Fallback: {config.llm.fallback.model}. max_hops: {config.graph.max_hops}. "
               f"agent.max_steps: {config.agent.max_steps}. Agents: productivity (real "
               "tools, empty temporary database) and research (real tools, internet)."), "",
              (f"**Overall: {'PASS' if passed else 'FAIL'}** (scored turns passed: "
               f"{sum(verdicts)}/{len(SCORED)})"), "",
              (f"Pass rule {PASS_RULE}: turn 1 runs the research agent, get_weather succeeds "
               "with a place containing 'pune', and the reply contains 'open-meteo'; turn 4 "
               "runs the productivity agent and never the research agent. Turns 2 and 3 are "
               "recorded only."), ""]
    report.write_text("\n".join(header + lines) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # replies may contain emoji
    print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
