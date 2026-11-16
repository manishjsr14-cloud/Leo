"""Tool results written out as one short plain-English line, by code (M1.7 run4).

The responder gets this line next to the raw result, with dates and times
already in words, so it does not have to read ISO times itself (run3: a move
to 17:00-18:00 was reported as "5:00 to 7:00 pm"). Example:
  move_event -> "Moved 'Team meeting' to Mon 16 Nov, 5:00-6:00 pm"
A result with an unexpected shape gets no line (the raw result is still sent).
"""

from typing import Any

from leo.language.say_time import say_iso_span


# One event as "'Gym', Sat 21 Nov, 8:00-9:00 am".
def event_words(event: dict) -> str:
    return f"'{event['title']}', {say_iso_span(event['start'], event['end'])}"


# The calendar tools.
def calendar_words(tool: str, result: Any) -> str | None:
    if tool == "create_event":
        return f"Created {event_words(result)}"
    if tool == "move_event":
        return f"Moved '{result['title']}' to {say_iso_span(result['start'], result['end'])}"
    if tool == "cancel_event":
        return f"Cancelled event {result['cancelled']}"
    if tool == "get_events":
        if not result:
            return "No events in that time"
        return f"{len(result)} event(s): " + "; ".join(event_words(e) for e in result)
    if tool == "find_free_slots":
        if not result:
            return "No free time in that range"
        return "Free: " + "; ".join(say_iso_span(s["start"], s["end"]) for s in result)
    return None


# The productivity tools.
def productivity_words(tool: str, result: Any) -> str | None:
    if tool == "add_task":
        return f"Added task '{result['title']}'"
    if tool == "complete_task":
        return f"Marked task '{result['title']}' as done"
    if tool == "list_tasks":
        titles = ", ".join(f"'{t['title']}'" for t in result)
        return f"{len(result)} open task(s): {titles}" if result else "No open tasks"
    if tool == "add_note":
        return "Saved the note"
    if tool == "list_notes":
        return f"{len(result)} note(s)"
    if tool == "start_timer":
        return f"Timer '{result['label']}' set for {result['minutes']} minute(s)"
    if tool == "calculate":
        return f"{result['expression']} = {result['result']}"
    return None


# The research tools.
def research_words(tool: str, result: Any) -> str | None:
    if tool == "get_weather":
        days = "; ".join(f"{d['day']} {d['date']}: {d['rain_chance_pct']}% chance of rain, "
                         f"{d['rain_mm']} mm" for d in result["days"])
        return f"Weather for {result['place']} ({result['source']}): {days}"
    if tool == "web_search":
        return f"{len(result['results'])} search result(s) from {result['source']}"
    if tool == "read_page":
        return f"Read the page {result['url']}"
    return None


# The line for one successful tool call, or None when there is none.
def result_in_words(tool: str, result: Any) -> str | None:
    try:
        for words in (calendar_words, productivity_words, research_words):
            line = words(tool, result)
            if line is not None:
                return line
    except (KeyError, TypeError, ValueError):
        return None
    return None
