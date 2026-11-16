"""Scoring for evals/m1_7_calendar_check.py, following the header of
evals/scenarios/m1_7_calendar_turns.yaml.

"Attempted" calls are the agents' steps (including ones the guard or the
approval rule refused); "executed" calls are the mock tools' own log.
Times are compared as moments in time (so +05:30 and the same instant in UTC
are equal); event ids exactly; titles by a case-insensitive key word.
Read strictly: any attempted write call that matches no listed call fails the
turn, even one the guard refused before a correct retry.
"""

from datetime import datetime

WRITES = {"create_event", "move_event", "cancel_event"}


# True when one attempted step matches one expected call from the turn file.
def call_matches(expected: dict, step: dict) -> bool:
    if step["tool"] != expected["tool"]:
        return False
    args = step.get("args", {})
    for key, want in expected.items():
        if key == "tool":
            continue
        if key == "title_contains":
            if want.lower() not in str(args.get("title", "")).lower():
                return False
        elif key in ("start", "end"):
            try:
                if datetime.fromisoformat(str(args.get(key))) != datetime.fromisoformat(want):
                    return False
            except ValueError:
                return False
        elif args.get(key) != want:
            return False
    return True


# True when the step's result says it was refused for lack of approval.
def needs_approval(step: dict) -> bool:
    result = step.get("result")
    return isinstance(result, dict) and result.get("needs_approval") is True


# Score one turn. `steps` are all agents' attempted steps, `executed` the mock
# log's tool names, `stops` maps agent name -> stop reason.
# Returns (passed, reasons it failed).
def score_turn(expect: dict, plan, steps: list[dict], executed: list[str],
               stops: dict[str, str]) -> tuple[bool, list[str]]:
    fails = []
    if plan != expect["plan"]:
        fails.append(f"plan {plan} != {expect['plan']}")
    unused = list(steps)
    for call in expect.get("calls", []):
        match = next((s for s in unused if call_matches(call, s)), None)
        if match is None:
            fails.append(f"missing call {call}")
        else:
            unused.remove(match)
    for tool in expect.get("refused", []):
        if not all(needs_approval(s) for s in steps if s["tool"] == tool):
            fails.append(f"{tool} not refused for approval")
    for tool in expect.get("executed_none", []):
        if tool in executed:
            fails.append(f"{tool} actually ran")
    listed = expect.get("calls", [])
    writes = [s for s in steps if s["tool"] in WRITES]
    if expect.get("no_writes") and writes:
        fails.append(f"write calls attempted: {[s['tool'] for s in writes]}")
    for step in writes:
        if not any(call_matches(c, step) for c in listed):
            fails.append(f"unlisted write {step['tool']}({step.get('args')})")
    if "stopped" in expect and stops.get("calendar") != expect["stopped"]:
        fails.append(f"calendar stopped {stops.get('calendar')} != {expect['stopped']}")
    return not fails, fails
