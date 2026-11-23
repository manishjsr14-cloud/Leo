"""The reply written by code when an event was held back by its condition (M1 exit check).

"Agar Saturday ko baarish nahi hogi to ... trip plan kar do": when the
forecast says rain, or the condition cannot be checked, the calendar agent
adds nothing (leo/agents/calendar_condition.py). The reply then comes from
the templates in prompts/replies.yaml, in English or Hinglish, with no LLM
call, so it always names the forecast or asks to confirm:
  1. cancels waiting for approval, named by event (if the message also cleared a range);
  2. why the event was not added: the rain chance, no forecast, or a condition
     code cannot check (these two end with a question).
Only for the calendar agent, alone or after the research agent; anything else,
and Hindi (Devanagari) messages, go to the LLM responder.
"""

from datetime import datetime

from leo.graph.result_words import listed_events
from leo.graph.state import LeoState
from leo.language.say_time import say_clock, say_day, say_iso_span
from leo.llm.prompts import load_prompt


# "'Gym' (Sat 21 Nov, 8:00-9:00 am) and 'Call' (...)" for the events waiting for approval.
def waiting_events(outcome: dict, joiner: str) -> str:
    events = listed_events(outcome.get("steps", []))
    ids = (outcome.get("approval") or {}).get("event_ids", [])
    named = [f"'{events[i]['title']}' ({say_iso_span(events[i]['start'], events[i]['end'])})"
             for i in ids if i in events]
    return f" {joiner} ".join(named)


# The code-written reply for a held event, or None when the LLM responder must answer.
def held_reply(state: LeoState) -> str | None:
    language, results = state.get("language"), state.get("agent_results") or {}
    outcome = results.get("calendar")
    if language not in ("en", "hinglish") or not isinstance(outcome, dict):
        return None
    hold = outcome.get("held")
    if not hold or set(results) - {"research", "calendar"}:
        return None
    templates = load_prompt("replies").extra(language)
    start = datetime.fromisoformat(hold["start"])
    parts = []
    events = waiting_events(outcome, templates["and"])
    if events:
        parts.append(templates["needs_approval"].format(events=events))
    parts.append(templates[f"held_{hold['why']}"].format(
        day=say_day(start), clock=say_clock(start), pct=hold.get("rain_pct")))
    return " ".join(parts)
