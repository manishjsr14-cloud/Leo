"""Dates and times written out in plain English, by code (M1.7).

say_span(start, end) -> "Mon 16 Nov, 5:00-6:00 pm". Used in the calendar
agent's prompt and in the responder's result lines, so neither model has to
turn an ISO time into words (run3 showed "5:00 to 7:00 pm" for 17:00-18:00).
"""

from datetime import datetime


# "Mon 16 Nov".
def say_day(moment: datetime) -> str:
    return f"{moment:%a} {moment.day} {moment:%b}"


# "5:00" and "pm" for a moment.
def clock_parts(moment: datetime) -> tuple[str, str]:
    return f"{moment.hour % 12 or 12}:{moment.minute:02d}", "am" if moment.hour < 12 else "pm"


# "5:00 pm".
def say_clock(moment: datetime) -> str:
    return " ".join(clock_parts(moment))


# "Mon 16 Nov, 5:00-6:00 pm", "Mon 16 Nov, 11:00 am-1:00 pm", or two days when
# the span crosses midnight; a span of whole days reads "Mon 16 Nov to Sun 22 Nov".
def say_span(start: datetime, end: datetime) -> str:
    if start.hour == start.minute == end.hour == end.minute == 0:
        last = end.toordinal() - start.toordinal()
        if last == 1:
            return f"{say_day(start)} (whole day)"
        return f"{say_day(start)} to {say_day(datetime.fromordinal(end.toordinal() - 1))}"
    if start.date() != end.date():
        return f"{say_day(start)}, {say_clock(start)} to {say_day(end)}, {say_clock(end)}"
    return f"{say_day(start)}, {say_clock_span(start, end)}"


# "5:00-6:00 pm" or "11:00 am-1:00 pm": two times on one day, without the day.
def say_clock_span(start: datetime, end: datetime) -> str:
    (a, a_half), (b, b_half) = clock_parts(start), clock_parts(end)
    return f"{a}-{b} {b_half}" if a_half == b_half else f"{a} {a_half}-{b} {b_half}"


# say_span for two ISO strings (tool results carry times as text).
def say_iso_span(start: str, end: str) -> str:
    return say_span(datetime.fromisoformat(start), datetime.fromisoformat(end))
