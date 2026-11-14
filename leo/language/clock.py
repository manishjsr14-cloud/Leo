"""Clock and duration reading for the Indian time parser (time_parser.py).

find_clock reads "sava teen baje", "4:30 pm", "11 am"; to_24h applies
subah/shaam/raat and the default am/pm; find_duration reads "2 ghante baad"
and "15 minute pehle". Kept apart from time_parser.py so each file stays short.
"""

from fractions import Fraction

from leo.language import time_words as w
from leo.language.numbers import number_at


# The amount just before the unit at words[u], as (value, first index), or None.
# "a"/"an" count as 1 ("an hour") and "half an" as 1/2 ("half an hour").
def amount_before(words: list[str], u: int) -> tuple[Fraction, int] | None:
    if u >= 1 and words[u - 1] in ("a", "an"):
        if u >= 2 and words[u - 2] == "half":
            return Fraction(1, 2), u - 2
        return Fraction(1), u - 1
    for start in (u - 2, u - 1):                 # longer first: "sava do ghante" = 2.25
        read = number_at(words, start) if start >= 0 else None
        if read is not None and read[1] == u:
            return read[0], start
    return None


# Find "<number> <unit>" with a word that says after/before; returns
# (kind, minutes, first index, last index) or None. kind is "after" or "before".
def find_duration(words: list[str]) -> tuple[str, int, int, int] | None:
    for u, word in enumerate(words):
        amount = amount_before(words, u) if word in w.UNITS else None
        if amount is None:
            continue
        minutes, start = int(amount[0] * w.UNITS[word]), amount[1]
        following = words[u + 1] if u + 1 < len(words) else ""
        if following in w.BEFORE_WORDS:
            return "before", minutes, start, u + 1
        if following in w.AFTER_WORDS or (start > 0 and words[start - 1] in w.IN_WORDS):
            return "after", minutes, start, u + 1
    return None


# The clock hour in the text as (hours, minutes, am/pm word or ""), or None.
def find_clock(words: list[str]) -> tuple[int, int, str] | None:
    for i, word in enumerate(words):
        if ":" in word:
            hours, minutes = word.split(":")
            after = words[i + 1] if i + 1 < len(words) else ""
            return int(hours), int(minutes), after if after in ("am", "pm") else ""
        read = number_at(words, i)
        if read is None or read[1] >= len(words):
            continue
        value, end = read
        if words[end] in w.HOUR_MARKERS or words[end] in ("am", "pm"):
            hours = int(value)
            minutes = int((value - hours) * 60)
            ampm = words[end] if words[end] in ("am", "pm") else ""
            return hours or 12, minutes, ampm             # "paune ek" = 12:45
    return None


# Turn a 12-hour clock into 24-hour time; also says whether the default was
# used and whether the time falls early next morning ("raat 2 baje").
def to_24h(hours: int, ampm: str, period: str | None) -> tuple[int, bool, bool]:
    if hours >= 13 or hours == 0:
        return hours % 24, False, False
    if ampm:
        return hours % 12 + (12 if ampm == "pm" else 0), False, False
    if period == "morning":
        return hours % 12, False, False
    if period == "night":
        early = hours == 12 or hours <= 4
        return (hours % 12, False, True) if early else (hours + 12, False, False)
    if period == "evening" or (period == "afternoon" and hours <= 7):
        return (12 if hours == 12 else hours + 12), False, False
    if period == "afternoon":
        return hours, False, False                         # "dopahar 11 baje", "dopahar 12"
    return (hours + 12 if hours <= 7 else hours), True, False
