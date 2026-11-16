"""M1.7 calendar check. Runs each turn of evals/scenarios/m1_7_calendar_turns.yaml
alone (a new conversation) through the real graph and the real LLM gateway,
with MOCK tools only: the turn file's calendar events and weather, and mock
productivity tools. "now" is fixed by the turn file. Writes a new report with,
per turn: plan, attempted and executed tool calls, stop reasons, LLM calls,
time, reply, the verdict and why, and the (unscored) reply note. From run3 it
also records the first JSON key of every agent step reply (not scored).

  python -m evals.m1_7_calendar_check evals/reports/m1.7_calendar_check_<date>.md

No personal data is used and nothing touches a real calendar.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

from evals.m1_4_check_helpers import CountingChat, call_label
from evals.m1_5_check_helpers import chosen, tagged
from evals.m1_7_scoring import score_turn
from leo import cli
from leo.agents.calendar import calendar_agent
from leo.agents.productivity import productivity_agent
from leo.agents.research import research_agent
from leo.config import load_config
from leo.graph.builder import build_graph
from leo.llm.gateway import LLMUnavailable
from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.mock.productivity import mock_productivity_tools
from leo.tools.mock.research import mock_research_tools
from leo.tools.registry import by_name

TURNS_FILE = Path("evals/scenarios/m1_7_calendar_turns.yaml")


# The current commit and whether the working tree has uncommitted changes.
def git_state() -> str:
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          check=False, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"],
                           check=False, capture_output=True, text=True).stdout.strip()
    return head + (" (uncommitted changes present)" if dirty else "")


# The first key of a step reply as the model wrote it, "(not JSON)" if it is not
# a JSON object.
def first_key(text: str) -> str:
    try:
        data = json.loads(text)
    except ValueError:
        return "(not JSON)"
    return next(iter(data), "(empty)") if isinstance(data, dict) else "(not JSON)"


# Run one turn on a fresh graph and mock tools. Returns its report row and details.
def run_one(turn: dict, data: dict, config, now: datetime) -> tuple[bool, str, list[str]]:
    chat, log, runs, steps = CountingChat(), [], [], config.agent.max_steps
    calendar = by_name(mock_calendar_tools(log, data["mock_calendar"]))
    web = by_name(mock_research_tools(log, data["mock_weather"]))
    tasks = by_name(mock_productivity_tools(log))
    agents = {
        "productivity": tagged(productivity_agent(chat, tasks, steps), "productivity", runs),
        "research": tagged(research_agent(chat, web, steps, today=lambda: now.date()),
                           "research", runs),
        "calendar": tagged(calendar_agent(chat, calendar, steps, config.calendar,
                                          now=lambda: now), "calendar", runs)}
    graph = build_graph(chat, agents=agents, config=config)
    start = time.perf_counter()
    try:
        text = cli.run_turn(graph, [], turn["text"], False)[0].content
    except LLMUnavailable as error:  # both models failed: report it
        text = f"FAILED: {error!r}"
    wall = time.perf_counter() - start
    plans = chosen(chat.calls)
    plan = plans[0] if plans else None
    attempted = [s for _, outcome in runs for s in outcome["steps"]]
    stops = {name: outcome["stopped"] for name, outcome in runs}
    passed, fails = score_turn(turn["expect"], plan, attempted, [c.tool for c in log], stops)
    verdict = "PASS" if passed else "FAIL"
    keys = [first_key(c["text"]) for c in chat.calls if c["node"] == "agent"]
    row = (f"| {turn['id']} | {plan} | {', '.join(s['tool'] for s in attempted) or 'none'} | "
           f"{', '.join(c.tool for c in log) or 'none'} | {', '.join(keys) or 'none'} | "
           f"{len(chat.calls)} | {wall:.1f} | {verdict} |")
    details = [f"### {turn['id']}: {verdict}", "", f"**You:** {turn['text']}", "",
               f"**Leo:** {text}", "", f"Plan: {plan}; stops: {stops or 'no agent run'}", "",
               "LLM calls: " + ", ".join(call_label(c) for c in chat.calls), "",
               "Agent step replies:"]
    details += [f"- first key `{first_key(c['text'])}`: `{c['text']}`"
                for c in chat.calls if c["node"] == "agent"] or ["- none"]
    details += ["", "Attempted tool calls (agent steps):"]
    details += [f"- `{s['tool']}({s['args']})` -> `{s['result']}`" for s in attempted] or [
        "- none"]
    details += ["", "Executed (mock log): " + (", ".join(c.tool for c in log) or "none"), ""]
    details += [f"Why it failed: {'; '.join(fails)}", ""] if fails else []
    if turn.get("reply_note"):
        details += [f"Reply note (not scored, for a human): {turn['reply_note']}", ""]
    return passed, row, details


# Write a new report; refuse to overwrite an earlier one.
def main() -> None:
    report = Path(sys.argv[1])
    if report.exists():
        sys.exit(f"{report} already exists; earlier reports are never rewritten.")
    config = load_config()
    data = yaml.safe_load(TURNS_FILE.read_text(encoding="utf-8"))
    now = datetime.fromisoformat(data["now"])
    results = [run_one(turn, data, config, now) for turn in data["turns"]]
    passed = sum(1 for ok, _, _ in results if ok)
    header = [f"# M1.7 calendar check — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
              f"Commit: {git_state()}. Turn file: {TURNS_FILE} (version {data['version']}).",
              (f"Local model: {config.llm.primary.model}. Fallback: "
               f"{config.llm.fallback.model}. agent.max_steps: {config.agent.max_steps}. "
               f"Fixed now: {data['now']}. All tools are mocks."), "",
              f"**Turns passed: {passed}/{len(results)}**", "",
              ("Scoring as in the turn file header; read strictly: an attempted write call "
               "that matches no listed call fails the turn even if the guard refused it."),
              "", ("| turn | plan | attempted | executed | first_keys | llm_calls | turn_s "
                   "| result |"), "|---|---|---|---|---|---|---|---|", *[row for _, row, _ in results], "",
              "## Details", ""]
    lines = header + [line for _, _, details in results for line in details]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # replies may contain emoji
    print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
