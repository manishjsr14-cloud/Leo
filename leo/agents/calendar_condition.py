"""A condition on adding an event, checked by code (architecture section 4.5, M1 exit check).

"Agar Saturday ko baarish nahi hogi to subah 7 baje Lonavala trip plan kar do":
the event is added only if the condition holds. Code decides, not the model:
  - a "no rain" condition ("agar baarish nahi", "if it won't rain"): the rain
    chance for the event's day comes from the research agent's get_weather
    result; above calendar.rain_skip_percent the event is not added ("rain");
    with no forecast for that day it is not added and the user is asked
    ("no_forecast");
  - any other "agar"/"if" condition: code cannot check it, so nothing is
    added and the user is asked to confirm ("condition").
The hold goes in the calendar outcome as "held"; the reply is written by code
(leo/graph/calendar_reply.py).
"""

from datetime import date, datetime

from leo.language.say_time import say_day
from leo.language.time_parser import split_words

CONDITION_WORDS = {"agar", "agr", "if", "yadi"}
RAIN_WORDS = {"baarish", "barish", "barsaat", "rain", "rains", "raining", "rainy"}
NOT_WORDS = {"nahi", "nahin", "na", "not", "no", "won", "wont", "doesn", "don", "dont", "isn"}


# The rain chance (%) for `day` from a successful get_weather in the research results.
def rain_chance(results: dict, day: date) -> int | None:
    research = results.get("research")
    steps = research.get("steps", []) if isinstance(research, dict) else []
    for step in steps:
        result = step.get("result")
        if step["tool"] != "get_weather" or not isinstance(result, dict):
            continue
        for forecast in result.get("days", []):
            if forecast.get("date") == day.isoformat():
                return int(forecast["rain_chance_pct"])
    return None


# Why the event at `start` must not be added now, or None when it may be.
# Returns {"why": "rain" | "no_forecast" | "condition", "start": ISO, ...}.
def create_hold(text: str, start: datetime, results: dict, limit: int) -> dict | None:
    words = set(split_words(text))
    if not words & CONDITION_WORDS:
        return None
    hold = {"start": start.isoformat()}
    if not (words & RAIN_WORDS and words & NOT_WORDS):
        return {**hold, "why": "condition"}
    chance = rain_chance(results, start.date())
    if chance is None:
        return {**hold, "why": "no_forecast"}
    if chance > limit:
        return {**hold, "why": "rain", "rain_pct": chance, "limit": limit}
    return None


# One fact line for the responder about a held event.
def hold_words(hold: dict) -> str:
    day = say_day(datetime.fromisoformat(hold["start"]))
    if hold["why"] == "rain":
        return (f"create_event NOT done: the forecast for {day} shows {hold['rain_pct']}% "
                f"chance of rain (more than {hold['limit']}%), so the event was not added")
    if hold["why"] == "no_forecast":
        return (f"create_event NOT done: no forecast for {day}, so the rain condition could "
                "not be checked; ask the user whether to add it anyway")
    return ("create_event NOT done: the request has a condition code cannot check; "
            "ask the user to confirm before adding it")
