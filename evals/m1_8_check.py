"""M1.8 language and reply check. Runs each turn of
evals/scenarios/m1_8_language_turns.yaml alone (a new conversation) through the
real graph and the real LLM gateway, with MOCK tools only. Writes a new report
with the machine, language and reply checks, tool checks, LLM calls, prompt
tokens, times per turn, and the done rule worked out from the turn file.

  python -m evals.m1_8_check <report.md> <label> [<baseline report.md>]

<label> is "baseline" (the pre-M1.8 code) or "run1"/"run2". Without a baseline
report, done-rule item 5 cannot be worked out and is reported as not checked.
No personal data is used and nothing touches a real calendar.
"""

import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

from evals.m1_5_check_helpers import tagged
from evals.m1_7_calendar_check import git_state
from evals.m1_8_check_helpers import (
    TimedChat,
    baseline_calls,
    baseline_machine,
    call_label,
    node_summary,
)
from evals.m1_8_scoring import all_calls_attempted, language_ok, reply_fails, tool_fails
from evals.machine import machine_line
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

TURNS_FILE = Path("evals/scenarios/m1_8_language_turns.yaml")
ISSUE_TURNS = {"I01", "I02", "I03", "I04", "I05"}


# Run one turn on a fresh graph and mock tools. Returns a dict with everything found.
def run_one(turn: dict, data: dict, config, now: datetime, memory=None) -> dict:
    chat, log, runs, steps = TimedChat(), [], [], config.agent.max_steps
    calendar = by_name(mock_calendar_tools(log, data["mock_calendar"]))
    web = by_name(mock_research_tools(log, data["mock_weather"]))
    tasks = by_name(mock_productivity_tools(log))
    agents = {
        "productivity": tagged(productivity_agent(chat, tasks, steps), "productivity", runs),
        "research": tagged(research_agent(chat, web, steps, today=lambda: now.date()),
                           "research", runs),
        "calendar": tagged(calendar_agent(chat, calendar, steps, config.calendar,
                                          now=lambda: now), "calendar", runs)}
    graph = build_graph(chat, agents=agents, config=config, memory=memory)  # memory: M2.3b
    start = time.perf_counter()
    try:
        reply = str(cli.run_turn(graph, [], turn["text"], False)[0].content)
    except LLMUnavailable as error:  # both models failed: report it
        reply = f"FAILED: {error!r}"
    wall = time.perf_counter() - start
    # The plan is the agents that actually ran, in order, read from the graph
    # run (M1 exit check runner fix): a plan made by code has no supervisor LLM
    # reply, so reading only that reply (chosen) recorded [] for those turns.
    plans = [[name for name, _ in runs]]
    attempted = [s for _, outcome in runs for s in outcome["steps"]]
    stops = {name: outcome["stopped"] for name, outcome in runs}
    tool_text = " ".join(str(s.get("result")) for s in attempted)
    lang_pass, lang_why = language_ok(reply, turn["lang"], tool_text)
    tools = tool_fails(turn, plans[0] if plans else None, attempted, [c.tool for c in log], stops)
    return {"turn": turn, "reply": reply, "wall": wall, "calls": chat.calls, "plan": plans,
            "steps": attempted, "stops": stops, "lang": (lang_pass, lang_why),
            "reply_fails": reply_fails(reply, turn, attempted), "tool_fails": tools}


# The done rule from the turn file header, item by item: (text, passed or None).
def done_items(results: list[dict], base: dict[str, int] | None) -> list[tuple[str, bool | None]]:
    language = [r for r in results if r["turn"]["id"].startswith("L")]
    lang_right = sum(r["lang"][0] for r in language)
    devanagari = [r["turn"]["id"] for r in results
                  if any(f.startswith("no_devanagari") for f in r["reply_fails"])]
    issues = [r["turn"]["id"] for r in results if r["reply_fails"]
              or (r["turn"]["id"] in ISSUE_TURNS and r["tool_fails"])]
    multi = [r["turn"]["id"] for r in results if r["turn"].get("multi_step")
             and not all_calls_attempted(r["tool_fails"])]
    items = [(f"1. language correct on {lang_right}/{len(language)} (need 18)", lang_right >= 18),
             (f"2. Devanagari replies to Roman text: {devanagari or 'none'}", not devanagari),
             (f"3. turns failing an issue rule: {issues or 'none'}", not issues),
             (f"4. multi_step turns missing a call: {multi or 'none'}", not multi)]
    if base is None:
        return items + [("5. fewer LLM calls than baseline: not checked (no baseline)", None)]
    single = [r for r in results if r["turn"].get("single_step")]
    slower = [f"{r['turn']['id']} {len(r['calls'])} vs {base.get(r['turn']['id'])}"
              for r in single if len(r["calls"]) >= base.get(r["turn"]["id"], 0)]
    return items + [(f"5. single_step turns NOT using fewer calls: {slower or 'none'}",
                     not slower)]


# The report row and detail lines for one turn.
def turn_lines(r: dict) -> tuple[str, list[str]]:
    t, calls = r["turn"], r["calls"]
    tokens = sum(c["prompt_tokens"] or 0 for c in calls)
    first = sum(c["first_token_s"] or 0 for c in calls)
    row = (f"| {t['id']} | {t['lang']} | {'ok' if r['lang'][0] else 'FAIL'} | "
           f"{'ok' if not r['reply_fails'] else 'FAIL'} | "
           f"{'ok' if not r['tool_fails'] else 'FAIL'} | {len(calls)} | {tokens} | "
           f"{first:.1f} | {r['wall']:.1f} |")
    details = [f"### {t['id']} ({t['lang']})", "", f"**You:** {t['text']}", "",
               f"**Leo:** {r['reply']}", "", f"Language: {r['lang'][1]}",
               f"Plan: {r['plan']}; stops: {r['stops'] or 'no agent run'}",
               "LLM calls: " + ", ".join(call_label(c) for c in calls), "", "Tool calls:"]
    details += [f"- `{s['tool']}({s['args']})` -> `{s['result']}`" for s in r["steps"]] or [
        "- none"]
    details += [f"- reply rule failed: {f}" for f in r["reply_fails"]]
    details += [f"- tool check failed: {f}" for f in r["tool_fails"]]
    return row, details + [""]


# Write a new report; refuse to overwrite an earlier one.
def main() -> None:
    report, label = Path(sys.argv[1]), sys.argv[2]
    base_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    if report.exists():
        sys.exit(f"{report} already exists; earlier reports are never rewritten.")
    machine = machine_line()
    if base_path and baseline_machine(base_path) != machine:
        sys.exit("The baseline report ran on another machine; runs are never compared across machines.")
    config, data = load_config(), yaml.safe_load(TURNS_FILE.read_text(encoding="utf-8"))
    now = datetime.fromisoformat(data["now"])
    results = [run_one(turn, data, config, now) for turn in data["turns"]]
    items = done_items(results, baseline_calls(base_path) if base_path else None)
    met = all(ok for _, ok in items) if all(ok is not None for _, ok in items) else None
    rows = [turn_lines(r) for r in results]
    header = [f"# M1.8 language check ({label}) — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
              machine, f"Commit: {git_state()}. Turn file: {TURNS_FILE} (version {data['version']}).",
              (f"Local model: {config.llm.primary.model}. Fallback: {config.llm.fallback.model}. "
               f"Fixed now: {data['now']}. All tools are mocks. Baseline: {base_path or 'none'}."),
              "", ("| turn | lang | lang_ok | reply_rules | tool_checks | llm_calls | "
                   "prompt_tokens | first_token_s | turn_s |"), "|---|---|---|---|---|---|---|---|---|",
              *[row for row, _ in rows], "",
              f"**Done rule met: {'yes' if met else 'no' if met is False else 'not checked'}**", "",
              *[f"- {'PASS' if ok else 'FAIL' if ok is False else 'n/a'}: {text}" for text, ok in items],
              "", "Prompt sizes per node (local model calls only):", "",
              *node_summary([c for r in results for c in r["calls"]]), "", "## Details", ""]
    lines = header + [line for _, details in rows for line in details]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # replies may contain emoji or Devanagari
    print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
