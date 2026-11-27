"""The plan rule for memory (M2.3b): code, not the model, keeps plans and events out.

A message that names a date or a time is a plan or an event ("kal mujhe Mumbai
jaana hai", "my flight is on 5 December") and is never stored as a memory.
It names one when:
  - the Indian time parser (leo/language/time_parser.py) reads a date or time,
  - it holds a day-and-month date ("5 December", "March 12"), which that
    parser does not read, or
  - it names a coming period: next week, agle hafte, this week, is hafte,
    next month, agle mahine.
  - it names a part of today or a coming weekend (M2.3b follow-up, the user's
    list plus "next weekend"): this morning / afternoon / evening / weekend,
    tonight, later today, is weekend, agle weekend, next weekend, aaj subah /
    dopahar / shaam / raat. It needs "this", "is", "agle", "next" or "aaj" in
    front, so a habit that names a part of the day ("in the evening", "raat
    ko", "on weekends") is not a plan.

Approved override (M2.3b proposal): a preference, habit or yearly word means a
lasting fact even with a time in it ("Mujhe meetings 11 baje ke baad pasand
hain", "Main roz subah 6 baje uthta hoon", "My mother's birthday is on 12 March").
Words fixed in the proposal, before any code.
"""

import re
from datetime import datetime

from leo.language.memory_words import words_of
from leo.language.time_parser import parse_time

MONTHS = (r"jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|"
          r"sep|sept|september|oct|october|nov|november|dec|december")
MONTH_DATE = re.compile(rf"\b(\d{{1,2}}(st|nd|rd|th)?\s+({MONTHS})|({MONTHS})\s+\d{{1,2}})\b")
COMING = re.compile(r"\b(next|this|agle|agla|agli|is) (week|hafte|hafta|month|mahine|mahina)\b")
TODAY_PART = re.compile(r"\b(this (morning|afternoon|evening|weekend)|tonight|later today"
                        r"|(is|agle|next) weekend|aaj (subah|dopahar|shaam|raat))\b")
LASTING = {"pasand", "prefer", "roz", "har", "every", "daily", "usually", "always", "hamesha",
           "birthday", "anniversary"}


# Which part of the time rule reads a date or time in the message, or None:
# "day-and-month date", "coming period", "part of today or weekend", "time parser".
def plan_reason(text: str, now: datetime) -> str | None:
    lowered = text.lower()
    if MONTH_DATE.search(lowered):
        return "day-and-month date"
    if COMING.search(lowered):
        return "coming period"
    if TODAY_PART.search(lowered):
        return "part of today or weekend"
    if parse_time(text, now).status != "not_understood":
        return "time parser"
    return None


# True when the message names a date or time: the parser reads one, or it has a
# day-and-month date, a coming period ("next week") or a part of today ("tonight").
def names_date_or_time(text: str, now: datetime) -> bool:
    return plan_reason(text, now) is not None


# True when a preference, habit or yearly word marks the message as lasting.
def says_lasting(text: str) -> bool:
    return any(w in LASTING for w in words_of(text))


# True when the message is a plan or an event, so it must not be stored.
def is_plan_or_event(text: str, now: datetime) -> bool:
    return names_date_or_time(text, now) and not says_lasting(text)
