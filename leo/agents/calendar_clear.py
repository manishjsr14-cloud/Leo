"""Clearing a range of the calendar, done by code (architecture section 4.5, M1 exit check).

"Saturday subah clear kar do" means: cancel every event in that range. The
model used to do this step by step and left events out (M1.7 t10, M1.8 I02,
M1.10 K04). Now code does it with no LLM call:
  1. get_events for the range the words name: the part of the day when they
     name one ("subah"), else the whole day; with no day it asks "Kis din ka?";
  2. one cancel_event per listed event, in time order. cancel_event is 🔴,
     so each call is refused until the user approves (human_approval, M2.5).
The refused cancels are kept together in the outcome's "approval" entry, so
the user is asked about them in one go.
Both calls go through call_tool with the calendar guard and code fill, as if
the model had made them.
"""

from leo.agents.calendar_fill import Range
from leo.agents.calendar_guard import ASK_DAY
from leo.agents.loop import code_step
from leo.ops import tracing
from leo.tools.base import Tool


# True when a step was refused only because it needs the user's approval.
def needs_approval(step: dict) -> bool:
    result = step["result"]
    return isinstance(result, dict) and result.get("needs_approval") is True


# Clear the range: list its events, then propose a cancel for each.
# Returns {"steps": [...], "summary": str, "stopped": "done" or "ask"} and,
# when cancels wait for approval, "approval": {"tool", "event_ids"}.
def clear_range(tools: dict[str, Tool], ranges: dict[str, Range]) -> dict:
    name = next((n for n in ("window", "day") if n in ranges), None)
    if name is None:
        return {"steps": [], "summary": ASK_DAY, "stopped": "ask"}
    with tracing.span("clear range", "span", metadata={"by": "code", "range": name}):
        steps = [code_step(tools, "get_events", {"range": name})]
        listed = steps[0]["result"]
        if isinstance(listed, list):
            for event in sorted(listed, key=lambda e: e["start"]):
                steps.append(code_step(tools, "cancel_event", {"event_id": event["id"]}))
    out = {"steps": steps, "summary": "", "stopped": "done"}
    waiting = [s["args"]["event_id"] for s in steps if needs_approval(s)]
    if waiting:
        out["approval"] = {"tool": "cancel_event", "event_ids": waiting}
    return out
