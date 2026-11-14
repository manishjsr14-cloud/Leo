"""Helpers for evals/m1_5_cli_check.py: the supervisor's choices, a recorder
that keeps each agent run with its name, and the per-turn report lines.
"""

import json

from evals.m1_4_check_helpers import call_label


# The supervisor's choices in these LLM calls, e.g. ["research", "FINISH"].
def chosen(calls: list[dict]) -> list[str]:
    picks = []
    for call in calls:
        if call["node"] == "supervisor":
            try:
                picks.append(json.loads(call["text"]).get("next", "?"))
            except (ValueError, AttributeError):
                picks.append("invalid")
    return picks


# Report lines for one turn's details.
def turn_details(number, line, text, calls, picks, ran, stops, tools_run, ok) -> list[str]:
    lines = [f"### Turn {number}", "", f"**You:** {line}", "", f"**Leo:** {text}", "",
             f"Supervisor chose, in order: {picks or ['none']}; agents run: {ran or ['none']}",
             "", "LLM calls, in order: " + ", ".join(call_label(c) for c in calls), "",
             "Agent step replies:"]
    lines += [f"- `{c['text']}`" for c in calls if c["node"] == "agent"] or ["- none"]
    lines += ["", f"Stop reasons: {', '.join(stops) or 'no agent run'}", "", "Tool calls:"]
    lines += [f"- `{c.tool}({c.args})` -> `{c.result}`" for c in tools_run] or ["- none"]
    result = "recorded only" if ok is None else ("PASS" if ok else "FAIL")
    return lines + ["", f"Result: {result}", ""]


# Wrap an agent node so each run is kept in `runs` as (agent name, outcome).
def tagged(node, name: str, runs: list[tuple[str, dict]]):
    # Run the agent and keep its name and what it returned.
    def run(state, config):
        update = node(state, config)
        runs.append((name, update["agent_results"][name]))
        return update
    return run


