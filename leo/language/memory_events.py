"""The plan rule for memory (M2.3b): code, not the model, keeps plans and events out.

A message that names a date or a time is a plan or an event ("kal mujhe Mumbai
jaana hai", "my flight is on 5 December") and is never stored as a memory.
It names one when:
  - the Indian time parser (leo/language/time_parser.py) reads a date or time,
  - it holds a day-and-month date ("5 December", "March 12"), which that
    parser does not read, or
  - it names a coming period: next week, agle hafte, this week, is hafte,
    next month, agle mahine.
"weekend" is not in that list: "on weekends" is often a habit.

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
LASTING = {"pasand", "prefer", "roz", "har", "every", "daily", "usually", "always", "hamesha",
           "birthday", "anniversary"}


# True when the message names a date or time: the parser reads one, or it has a
# day-and-month date or a coming period ("next week", "agle hafte").
def names_date_or_time(text: str, now: datetime) -> bool:
    lowered = text.lower()
    if MONTH_DATE.search(lowered) or COMING.search(lowered):
        return True
    return parse_time(text, now).status != "not_understood"


# True when a preference, habit or yearly word marks the message as lasting.
def says_lasting(text: str) -> bool:
    return any(w in LASTING for w in words_of(text))


# True when the message is a plan or an event, so it must not be stored.
def is_plan_or_event(text: str, now: datetime) -> bool:
    return names_date_or_time(text, now) and not says_lasting(text)
