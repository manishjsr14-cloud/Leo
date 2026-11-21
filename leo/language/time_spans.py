"""Calendar times from the user's words, worked out in code (section 15.2, M1.7).

read_calendar_times builds on parse_time and adds what one parse result cannot hold:
  - a move with two times ("3 baje wali meeting 5 baje kar do"): the first
    time is the event's current start, the second its new start;
  - a part of the day ("Thursday dopahar"): a time range from
    config.yaml calendar.day_parts, for get_events and find_free_slots.
The model never works out dates or times; the calendar agent shows it these.
Not handled: "raat 1-4 baje" as the NEW time of a move stays on the same date.
"""

from datetime import date, datetime, time, timedelta
from typing import Literal

from pydantic import BaseModel

from leo.config import CalendarConfig
from leo.language import time_words as w
from leo.language.clock import find_clocks, to_24h
from leo.language.time_parser import parse_time, split_words

# Questions asked back (Hinglish; the responder rewrites them in the user's language).
TOO_MANY_TIMES = "Message mein do se zyada time hain. Kaunsa time chahiye?"
TWO_DAYS = "Do alag din likhe hain. Meeting abhi kis din hai, aur kis din le jaani hai?"


class CalendarTimes(BaseModel):
    """Times taken from the user's words. All datetimes are in IST."""

    status: Literal["ok", "ask", "none"]       # none: no date or time in the words
    question: str | None = None                # set when status is "ask"
    start: datetime | None = None              # event start (for a move: the new start)
    move_from: datetime | None = None          # a move's current start (first of two times)
    window: tuple[datetime, datetime] | None = None   # part-of-day range, e.g. dopahar
    day: tuple[datetime, datetime] | None = None      # the whole day the words name
    assumed_ampm: bool = False                 # am/pm of the (new) start was assumed (M1.8)


# A key per day word in the text ("kal", "parso", a weekday number, ...).
def day_keys(words: list[str]) -> set:
    groups = {"today": w.TODAY, "kal": w.KAL, "tomorrow": w.TOMORROW,
              "yesterday": w.YESTERDAY, "parso": w.PARSO}
    keys = {name for name, group in groups.items() if set(words) & group}
    return keys | {w.WEEKDAY_OF[x] for x in words if x in w.WEEKDAY_OF}


# The part of the day for the clock at index i: the last period word before it,
# else `fallback` (the first period word in the text, as parse_time uses).
def period_before(words: list[str], i: int, fallback: str | None) -> str | None:
    found = [w.PERIODS[x] for x in words[:i] if x in w.PERIODS]
    return found[-1] if found else fallback


# The window for the first part-of-day word in the text on `day`, or None.
def day_window(words: list[str], day: date, zone, config: CalendarConfig):
    period = next((w.PERIODS[x] for x in words if x in w.PERIODS), None)
    if period is None or period not in config.day_parts:
        return None
    first, last = config.day_parts[period]
    midnight = datetime.combine(day, time(0), zone)
    return midnight + timedelta(hours=first), midnight + timedelta(hours=last)


# Read the calendar times in `text`. `now` must carry the time zone (IST).
def read_calendar_times(text: str, now: datetime, config: CalendarConfig) -> CalendarTimes:
    parsed = parse_time(text, now)
    if parsed.status == "ask":
        return CalendarTimes(status="ask", question=parsed.question)
    if parsed.status == "not_understood":
        return CalendarTimes(status="none")
    zone, words = now.tzinfo, split_words(text)
    clocks = find_clocks(words)
    if len(clocks) > 2:
        return CalendarTimes(status="ask", question=TOO_MANY_TIMES)
    if len(clocks) == 2 and len(day_keys(words)) > 1:
        return CalendarTimes(status="ask", question=TWO_DAYS)
    midnight = datetime.combine(parsed.date, time(0), zone)
    found = CalendarTimes(status="ok", day=(midnight, midnight + timedelta(days=1)),
                          window=day_window(words, parsed.date, zone, config))
    if parsed.time is not None:
        found.start = datetime.combine(parsed.date, parsed.time, zone)
        found.assumed_ampm = parsed.assumed_ampm
    if len(clocks) == 2:
        hours, minutes, ampm, index = clocks[1]
        first_period = next((w.PERIODS[x] for x in words if x in w.PERIODS), None)
        new_hour, assumed, _ = to_24h(hours, ampm, period_before(words, index, first_period))
        found.move_from, found.assumed_ampm = found.start, assumed
        found.start = datetime.combine(parsed.date, time(new_hour, minutes), zone)
    return found
