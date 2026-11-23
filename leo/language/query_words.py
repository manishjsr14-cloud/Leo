"""A rule that spots "what is on my calendar then?" questions (M1 exit check, K07).

M1.8 L17 / M1.10 K07: "Aaj shaam 5 baje kya hai?" was planned to the research
agent. The trained intent router is Phase 6 (section 8.3); until then this
rule sends such a question straight to the calendar agent, with no LLM call.
It is deliberately narrow: the message must hold a query phrase ("kya hai",
"what's on", "what do I have") and a time word (a day, a part of the day or a
clock time), and EVERY other word must be a time word or a small filler word.
"Aaj shaam 5 baje kya hai?" and "What's on Saturday?" match; "Kal Pune mein
mausam kya hai?" does not ("pune", "mausam" are left over), nor does
"What is 15% of 3200?" (no query phrase, a number that is no clock time).
Anything that does not match goes to the supervisor's LLM as before.
"""

from leo.language import time_words as w
from leo.language.time_parser import split_words

# Query phrases, as split_words writes them ("what's" -> "what s").
QUERY_PHRASES = {"kya hai", "kya kya hai", "kya hain", "what s on", "whats on", "what is on",
                 "what do i have", "what have i got"}
QUERY_WORDS = {word for phrase in QUERY_PHRASES for word in phrase.split()}
FILLER = {"ko", "ka", "ke", "ki", "mera", "mere", "meri", "my", "on", "at", "for", "in", "the",
          "calendar", "schedule", "mein", "me", "pe", "par", "se", "tak", "wala", "wali"}
DAY_WORDS = w.TODAY | w.TOMORROW | w.KAL | w.PARSO | w.NEXT_WORDS | set(w.WEEKDAY_OF)
CLOCK_MARKERS = w.HOUR_MARKERS | {"am", "pm"}


# The time words of the message: day and part-of-day words, and numbers that are
# clock times ("5 baje", "5 pm", "5:30"). Returns None if a number is no clock time.
def time_words(words: list[str]) -> set[int] | None:
    found = set()
    for i, word in enumerate(words):
        if word in DAY_WORDS or word in w.PERIODS or word in CLOCK_MARKERS:
            found.add(i)
        elif word[0].isdigit():
            if ":" not in word and (i + 1 >= len(words) or words[i + 1] not in CLOCK_MARKERS):
                return None
            found.add(i)
    return found


# True when the message only asks what is on the calendar at a time.
def is_calendar_query(text: str) -> bool:
    words = split_words(text)
    joined = f" {' '.join(words)} "
    if "%" in text or not any(f" {p} " in joined for p in QUERY_PHRASES):
        return False
    timed = time_words(words)
    if not timed:  # no time word at all, or a number that is no clock time
        return False
    return all(i in timed or word in QUERY_WORDS | FILLER for i, word in enumerate(words))
