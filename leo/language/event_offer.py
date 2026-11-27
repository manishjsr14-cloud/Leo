"""When a plain statement names a coming event (M2.3c fix round a, the user's rule).

"Parso 4 baje interview hai" is a statement, so no agent runs (M2.3c). If it
holds an event word and a time the Indian time parser reads, Leo's code
(leo/graph/offer_reply.py) replies with an offer that shows what the parser
read, or with the parser's question when it asks ("kal" with no tense). The
model never writes that reply, and nothing is added.

No offer when the message holds a past-tense word ("Kal Rahul ka call aaya
tha") or the parsed date is before today. A time the parser cannot read
("this evening") gives no offer: the model replies as before. The word lists
were fixed in the approved fix-round proposal, before the code.
"""

from datetime import datetime

from leo.language import time_words as w
from leo.language.memory_words import words_of
from leo.language.time_parser import ParsedTime, parse_time

EVENT_WORDS = {"meeting", "call", "appointment", "flight", "train", "interview", "party",
               "dinner", "lunch", "class", "exam", "match", "wedding", "shaadi", "event"}
# "the" is left out on purpose: it is also the English article.
PAST_WORDS = {"tha", "thi", "aaya", "aayi", "aaye", "hua", "hui", "gaya", "gayi", "was", "were",
              "had", "yesterday", "last"}


# What the parser read for a statement that names a coming event: an "ok"
# result with a date from today on, or an "ask" result; None otherwise.
def event_time(text: str, now: datetime) -> ParsedTime | None:
    words = {word.removesuffix("'s") for word in words_of(text)}  # "doctor's" -> "doctor"
    if not words & EVENT_WORDS or words & PAST_WORDS:
        return None
    parsed = parse_time(text, now)
    if parsed.status == "ask":
        return parsed
    if parsed.status == "ok" and parsed.date is not None and parsed.date >= now.date():
        return parsed
    return None


# The part of the day the message names ("morning", "evening", ...), or None.
def part_of_day(text: str) -> str | None:
    return next((w.PERIODS[word] for word in words_of(text) if word in w.PERIODS), None)
