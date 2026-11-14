"""Indian time parser: Hinglish and Indian English dates and times (section 15.2).

parse_time("kal subah 10 baje meeting daal do", now) -> date 2026-11-15, time 10:00.
Rules only, no LLM: anything it cannot read comes back as not_understood, and
anything with two likely meanings comes back as ask, with a question.
Rules are listed in evals/scenarios/m1_6_indian_phrases.yaml.
"""

import datetime as dt
import re
from datetime import date, datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from leo.config import load_config
from leo.language import time_words as w
from leo.language.clock import find_clock, find_duration, to_24h


class ParsedTime(BaseModel):
    """What the parser understood. date/time are local (IST) values."""

    status: Literal["ok", "ask", "not_understood"]
    date: dt.date | None = None
    time: dt.time | None = None
    assumed_ampm: bool = False         # the 1-7 pm / 8-11 am / 12 noon default was used
    remind_before_min: int | None = None
    ask_about: Literal["kal", "midnight", "weekday"] | None = None
    question: str | None = None


# The current time in the configured zone (IST).
def current_time() -> datetime:
    return datetime.now(ZoneInfo(load_config().language.timezone))


# Lowercase words; "4:30" stays one word, "11am" becomes "11", "am".
def split_words(text: str) -> list[str]:
    return re.findall(r"\d{1,2}:\d{2}|\d+(?:\.\d+)?|[a-z]+", text.lower())


# Days from today given by day words, "ask:<reason>", or None when there are none.
def day_offset(words: list[str], now: datetime) -> int | str | None:
    text = " ".join(words)
    after = "day after tomorrow" in text
    if after:
        words = " ".join(words).replace("day after tomorrow", "").split()
    has = {name: bool(set(words) & group) for name, group in
           (("kal", w.KAL), ("tom", w.TOMORROW), ("yes", w.YESTERDAY), ("parso", w.PARSO))}
    if now.hour < 4 and (after or has["kal"] or has["tom"] or has["parso"]):
        return "ask:midnight"
    if after or has["parso"]:
        return 2
    if has["tom"] and has["yes"]:
        return "ask:kal"                                   # both words: unclear
    if has["kal"] and not (has["tom"] or has["yes"]):
        future = any(x in w.FUTURE_WORDS or x.endswith(w.FUTURE_ENDINGS) for x in words)
        past = any(x in w.PAST_WORDS for x in words)
        if future == past:
            return "ask:kal"                               # no signal, or both
        return 1 if future else -1
    if has["tom"]:
        return 1
    if has["yes"]:
        return -1
    return 0 if set(words) & w.TODAY else None


# Days from today for a weekday name, "ask:weekday", or None when there is none.
def weekday_offset(words: list[str], now: datetime) -> tuple[int | str, int] | None:
    for i, word in enumerate(words):
        if word in w.WEEKDAY_OF:
            target, today = w.WEEKDAY_OF[word], now.weekday()
            is_next = i > 0 and words[i - 1] in w.NEXT_WORDS
            if target == today or (is_next and target > today):
                return "ask:weekday", target
            return (target - today) % 7, target
    return None


# Build an ask result with its question.
def ask(reason: str, day: int | None = None) -> ParsedTime:
    question = w.QUESTIONS[reason].format(day=w.DAY_NAMES[day] if day is not None else "")
    return ParsedTime(status="ask", ask_about=reason, question=question)


# Read a date and time from Hinglish or Indian English text. `now` defaults to
# the current IST time; a naive `now` is taken as IST.
def parse_time(text: str, now: datetime | None = None) -> ParsedTime:
    zone = ZoneInfo(load_config().language.timezone)
    now = current_time() if now is None else now
    now = now.replace(tzinfo=zone) if now.tzinfo is None else now.astimezone(zone)
    words = split_words(text)
    remind = None
    duration = find_duration(words)
    if duration and duration[0] == "after":
        when = now + timedelta(minutes=duration[1])
        return ParsedTime(status="ok", date=when.date(), time=time(when.hour, when.minute))
    if duration:
        remind = duration[1]
        words = words[:duration[2]] + words[duration[3] + 1:]
    offset = day_offset(words, now)
    weekday = weekday_offset(words, now) if offset is None else None
    if isinstance(offset, str):
        return ask(offset.removeprefix("ask:"))
    if weekday and isinstance(weekday[0], str):
        return ask("weekday", weekday[1])
    days = offset if offset is not None else (weekday[0] if weekday else None)
    clock = find_clock(words)
    if days is None and clock is None:
        return ParsedTime(status="not_understood")
    found = ParsedTime(status="ok", remind_before_min=remind)
    day: date = now.date() + timedelta(days=days or 0)
    if clock:
        period = next((w.PERIODS[x] for x in words if x in w.PERIODS), None)
        hours, assumed, early = to_24h(clock[0], clock[2], period)
        found.time = time(hours, clock[1])
        found.assumed_ampm = assumed
        if days is not None and early:
            day += timedelta(days=1)                       # "kal raat 2 baje"
        if days is None and datetime.combine(day, found.time, zone) <= now:
            day += timedelta(days=1)                       # time already passed today
    found.date = day
    return found
