"""The reply written by code for a clear or a held event (M1 exit check, section 4.5).

When the calendar agent cleared a range (cancels waiting for approval,
leo/agents/calendar_clear.py) or held an event back by its condition
(leo/agents/calendar_condition.py), the reply comes from the templates in
prompts/replies.yaml, in English or Hinglish, with no LLM call. M1 exit
run4 showed the LLM responder leaving out the events waiting for approval.
The reply says, in this order, only what the tool results show:
  1. the forecast checked for the event's day (research get_weather);
  2. each event added, with its time (create_event);
  3. the events waiting for approval to be cancelled, by name and time;
  4. why an event was not added: rain, no forecast, or a condition code cannot
     check (the last two end with a question).
Only for the calendar agent, alone or after the research agent; anything else,
and Hindi (Devanagari) messages, go to the LLM responder.
"""

from datetime import datetime

from leo.agents.calendar_condition import rain_chance
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


# The events the calendar agent added in this run (successful create_event results).
def added_events(outcome: dict) -> list[dict]:
    return [s["result"] for s in outcome.get("steps", []) if s["tool"] == "create_event"
            and isinstance(s.get("result"), dict) and "error" not in s["result"]]


# The day the request is about: an added or held event's day, else the cleared range's.
def event_day(outcome: dict) -> datetime | None:
    starts = [e["start"] for e in added_events(outcome)]
    starts += [outcome["held"]["start"]] if outcome.get("held") else []
    starts += [s["args"]["start"] for s in outcome.get("steps", [])
               if s["tool"] == "get_events" and "start" in s.get("args", {})]
    return datetime.fromisoformat(starts[0]) if starts else None


# The code-written reply, or None when the LLM responder must answer.
def calendar_reply(state: LeoState) -> str | None:
    language, results = state.get("language"), state.get("agent_results") or {}
    outcome = results.get("calendar")
    if language not in ("en", "hinglish") or not isinstance(outcome, dict):
        return None
    hold = outcome.get("held")
    if not (hold or outcome.get("approval")) or set(results) - {"research", "calendar"}:
        return None
    templates, parts = load_prompt("replies").extra(language), []
    day = event_day(outcome)
    chance = rain_chance(results, day.date()) if day is not None else None
    if chance is not None and not (hold and hold["why"] == "rain"):
        parts.append(templates["forecast"].format(day=say_day(day), pct=chance))
    parts += [templates["added"].format(title=e["title"], when=say_iso_span(e["start"], e["end"]))
              for e in added_events(outcome)]
    events = waiting_events(outcome, templates["and"])
    if events:
        parts.append(templates["needs_approval"].format(events=events))
    if hold:
        start = datetime.fromisoformat(hold["start"])
        parts.append(templates[f"held_{hold['why']}"].format(
            day=say_day(start), clock=say_clock(start), pct=hold.get("rain_pct")))
    return " ".join(parts)
