"""The reply written by code for a "what's on" question (M1 cleanup item 4).

Used by leo/graph/quick_reply.py when the only agent step was one successful
get_events, in English or Hinglish, with no LLM call: every event is listed
with its time, in start order, so none can be left out. Events on one day
are listed under that day ("On Sat 21 Nov you have: 'Gym' (8:00-9:00 am) and
'Call' (10:00-10:30 am)."); events on several days each carry their day. An
empty result gives the "nothing on" reply for the range asked about.
Same pattern as the free-slot replies (free_reply in quick_reply.py).
"""

from datetime import datetime

from leo.language.say_time import say_clock_span, say_day, say_iso_span


# "a", "a and b", "a, b and c" with the template's word for "and".
def joined(items: list[str], word: str) -> str:
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} {word} {items[-1]}"


# The reply for a successful get_events result (a list of events).
def events_reply(step: dict, templates: dict) -> str:
    events = sorted(step["result"], key=lambda e: e["start"])
    if not events:
        args = step.get("args", {})
        return templates["no_events"].format(span=say_iso_span(args["start"], args["end"]))
    times = [(datetime.fromisoformat(e["start"]), datetime.fromisoformat(e["end"]))
             for e in events]
    one_day = len({start.date() for start, _ in times}) == 1
    said = [f"'{e['title']}' ({say_clock_span(a, b) if one_day else say_iso_span(e['start'], e['end'])})"
            for e, (a, b) in zip(events, times)]
    listed = joined(said, templates["and"])
    if one_day:
        return templates["events_on_day"].format(day=say_day(times[0][0]), events=listed)
    return templates["events_at"].format(events=listed)
