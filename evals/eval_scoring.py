"""Scoring for the M1.10 eval suite (evals/run_eval.py).

Reuses the M1.7 tool checks and the M1.8 reply and language rules (already
worked out per turn by evals/m1_8_check.run_one) and adds:
  - the regression rules of evals/scenarios/m1_10_known_failing.yaml
    (forbid_tools, no_refused, calc_numbers);
  - "no invented results": the reply must not claim a write that never
    succeeded. This is a fixed word-list heuristic, written before the first
    run: a success phrase counts only when no negation or condition word
    (NOT_CLAIM) is among the four words before it;
  - the list of refused calls (every attempted call that came back with an error);
  - the verdict of a turn: pass, fail, known_failing or fixed.
"""

import re

# Success phrase -> the tools that would make it true. Fixed with the suite.
CLAIMS = {
    "added": {"create_event", "add_task", "add_note"},
    "created": {"create_event", "add_task", "add_note"},
    "booked": {"create_event"},
    "daal diya": {"create_event", "add_task", "add_note"},
    "daal di": {"create_event", "add_task", "add_note"},
    "add kar diya": {"create_event", "add_task", "add_note"},
    "add ho gaya": {"create_event", "add_task", "add_note"},
    "schedule kar diya": {"create_event", "move_event"},
    "moved": {"move_event"},
    "rescheduled": {"move_event"},
    "shifted": {"move_event"},
    "move kar diya": {"move_event"},
    "shift kar diya": {"move_event"},
    "cancelled": {"cancel_event"},
    "canceled": {"cancel_event"},
    "cancel kar diya": {"cancel_event"},
    "cancel kar di": {"cancel_event"},
    "cancel ho gaya": {"cancel_event"},
    "hata diya": {"cancel_event"},
    "marked as done": {"complete_task"},
    "marked as complete": {"complete_task"},
    "complete kar diya": {"complete_task"},
    "noted": {"add_note"},
    "note kar liya": {"add_note"},
    "likh liya": {"add_note"},
    "timer set": {"start_timer"},
    "timer started": {"start_timer"},
    "timer laga diya": {"start_timer"},
}
NOT_CLAIM = {"not", "nahi", "nahin", "never", "t", "will", "would", "can", "could", "once",
             "after", "before", "until", "approve", "approval", "if", "agar", "be", "should"}


# The steps whose result is an error (guard, bad arguments, approval, a question).
def refused_calls(steps: list[dict]) -> list[str]:
    found = []
    for step in steps:
        result = step.get("result")
        if not (isinstance(result, dict) and "error" in result):
            continue
        if result.get("needs_approval") is True:
            why = "needs approval"
        elif "ask" in result:
            why = "user must answer"
        else:
            why = f"error: {str(result['error'])[:80]}"
        found.append(f"{step['tool']} ({why})")
    return found


# Tools that ran without an error in this turn.
def succeeded(steps: list[dict]) -> set[str]:
    return {s["tool"] for s in steps
            if not (isinstance(s.get("result"), dict) and "error" in s["result"])}


# Success phrases in the reply for writes that never succeeded.
def invented_results(reply: str, steps: list[dict]) -> list[str]:
    low, ran, found = reply.lower(), succeeded(steps), []
    for phrase, tools in CLAIMS.items():
        for match in re.finditer(rf"\b{re.escape(phrase)}\b", low):
            before = re.findall(r"[a-z]+", low[:match.start()])[-4:]
            if tools & ran or NOT_CLAIM & set(before):
                continue
            found.append(f"no_invented: says {phrase!r} but none of {sorted(tools)} succeeded")
    return found


# Numbers written in a text, as floats ("15% of 3200" -> {15.0, 3200.0}).
def numbers_in(text: str) -> set[float]:
    return {float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)}


# The regression rules of one turn (forbid_tools, no_refused, calc_numbers).
def extra_fails(turn: dict, steps: list[dict]) -> list[str]:
    fails = [f"forbid_tools: {s['tool']} attempted" for s in steps
             if s["tool"] in turn.get("forbid_tools", [])]
    if turn.get("no_refused"):
        fails += [f"no_refused: {r}" for r in refused_calls(steps)]
    if "calc_numbers" in turn:
        first = next((s for s in steps if s["tool"] == "calculate"), None)
        want = {float(n) for n in turn["calc_numbers"]}
        if first is None:
            fails.append("calc_numbers: calculate never attempted")
        elif refused_calls([first]) or numbers_in(str(first["args"].get("expression"))) != want:
            fails.append(f"calc_numbers: first calculate was {first['args']} -> {first['result']}")
    return fails


# True when the turn has tool expectations beyond its plan.
def tools_scored(turn: dict) -> bool:
    rules = {"forbid_tools", "no_refused", "calc_numbers"}
    return bool(set(turn["expect"]) - {"plan"}) or bool(rules & set(turn))


# Score one run result (from m1_8_check.run_one) into a flat record.
def score(result: dict) -> dict:
    turn, steps = result["turn"], result["steps"]
    plan = result["plan"][0] if result["plan"] else None
    tool_fails = [f for f in result["tool_fails"] if not f.startswith("plan ")]
    tool_fails += extra_fails(turn, steps)
    invented = invented_results(result["reply"], steps)
    reply_fails = list(result["reply_fails"]) + invented
    record = {
        "routing_ok": plan == turn["expect"]["plan"],
        "tools_ok": not tool_fails if tools_scored(turn) else None,
        "lang_ok": result["lang"][0], "lang_why": result["lang"][1],
        "clock_ok": not any(f.startswith("clock_times") for f in reply_fails),
        "json_ok": not any(f.startswith("no_json") for f in reply_fails),
        "invented_ok": not invented,
        "reply_ok": result["lang"][0] and not reply_fails,
        "tool_fails": tool_fails, "reply_fails": reply_fails,
        "refused": refused_calls(steps)}
    record["passed"] = (record["routing_ok"] and record["tools_ok"] is not False
                        and record["reply_ok"])
    return record


# The verdict: a known failing turn that passes is "fixed".
def verdict(passed: bool, known: bool) -> str:
    if known:
        return "fixed" if passed else "known_failing"
    return "pass" if passed else "fail"
