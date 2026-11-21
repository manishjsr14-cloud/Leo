"""Clock times in a reply, for the M1.8 clock_times rule (evals/m1_8_scoring.py).

Each time found becomes a set of possible minutes after midnight, so that
17:00, 5 pm, 5:00 PM and "shaam 5 baje" all read as {1020}. A time with no
am/pm and no part-of-day word ("5 baje", "5:00") may be either: {300, 1020}.
Only numbers that look like clock times are read: with ":MM", or followed by
am/pm/baje, or written as a range ("5-6 pm", "5 se 6 baje"). Plain numbers
("10 minute", "18%", "17 Nov") are not times.
Written for this check only; Leo's own parser (leo/language/) is not used, so
the check does not grade Leo with Leo's code.
"""

import re

HOUR_WORDS = {"ek": 1, "do": 2, "teen": 3, "chaar": 4, "char": 4, "paanch": 5, "panch": 5,
              "chhe": 6, "chhah": 6, "che": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
              "gyarah": 11, "barah": 12}
FRACTIONS = {"sava": 15, "saadhe": 30, "sadhe": 30, "paune": -15}
WHOLE = {"dedh": (1, 30), "dhai": (2, 30), "dhaai": (2, 30)}
PERIODS = {"subah": "am", "morning": "am", "dopahar": "noon", "afternoon": "noon",
           "shaam": "pm", "sham": "pm", "evening": "pm", "raat": "night", "night": "night"}

NUM = r"(\d{1,2}|" + "|".join(HOUR_WORDS) + r")"
CLOCK = NUM + r"(?::(\d{2}))?"
MARK = r"(am|pm|baje|bje)"
RANGE = re.compile(rf"\b{CLOCK}\s*{MARK}?\s*(?:-|to|se|until|till)\s*{CLOCK}\s*{MARK}?")
SINGLE = re.compile(rf"\b{CLOCK}\s*{MARK}|\b(\d{{1,2}}):(\d{{2}})\b")
SPECIAL = re.compile(r"\b(dedh|dhai|dhaai)\s+(baje|bje)")


# Lowercase, "a.m." -> "am", dashes -> "-", so the patterns stay simple.
def clean(text: str) -> str:
    text = text.lower().replace("a.m.", "am").replace("p.m.", "pm")
    return re.sub(r"[–—]", "-", text)


# The part of the day named in the few words just before position `at`, or None.
def period_before(text: str, at: int) -> str | None:
    words = re.findall(r"[a-z]+", text[max(0, at - 30):at])
    found = [PERIODS[w] for w in words[-3:] if w in PERIODS]
    return found[-1] if found else None


# Possible minutes after midnight for hour h (as written), minutes m and a marker.
def candidates(h: int, m: int, mark: str | None, period: str | None) -> set[int]:
    if h > 12 or h == 0:                       # 24-hour clock: exact
        return {h % 24 * 60 + m}
    am, pm = h % 12 * 60 + m, (h % 12 + 12) * 60 + m
    if mark == "am" or period == "am":
        return {am}
    if mark == "pm" or period == "pm":
        return {pm}
    if period == "noon":
        return {pm}
    if period == "night":
        return {pm} if h >= 6 and h != 12 else {am}
    return {am, pm}


# The hour as a number ("5" or "paanch") and any fraction word just before it.
def hour_of(word: str, text: str, at: int) -> tuple[int, int]:
    hour = int(word) if word.isdigit() else HOUR_WORDS[word]
    before = re.findall(r"[a-z]+", text[max(0, at - 10):at])
    shift = FRACTIONS.get(before[-1], 0) if before else 0
    return (hour - 1, 45) if shift < 0 else (hour, shift)


# One clock time: candidates for hour word `h`, minute text `mm`, at position `at`.
def one_time(text: str, h: str, mm: str | None, mark: str | None, at: int) -> set[int]:
    hour, extra = hour_of(h, text, at)
    minutes = int(mm) if mm else extra
    mark = None if mark in ("baje", "bje") else mark
    return candidates(hour, minutes, mark, period_before(text, at))


# Every clock time in `text`, as (the text found, set of possible minutes).
def reply_times(text: str) -> list[tuple[str, set[int]]]:
    text, found = clean(text), []
    for match in RANGE.finditer(text):
        h1, m1, mark1, h2, m2, mark2 = match.groups()
        if not (mark1 or mark2 or m1 or m2):   # "5-6" alone is not a time
            continue
        end = one_time(text, h2, m2, mark2, match.start(4))
        start = one_time(text, h1, m1, mark1 or mark2, match.start())
        if mark1 is None and mark2 in ("am", "pm"):   # "11-1 pm": start may be either
            start |= one_time(text, h1, m1, None, match.start())
        found += [(match.group(0), start), (match.group(0), end)]
        text = text[:match.start()] + " " * len(match.group(0)) + text[match.end():]
    for match in SPECIAL.finditer(text):
        hour, minutes = WHOLE[match.group(1)]
        found.append((match.group(0), candidates(hour, minutes, None,
                                                 period_before(text, match.start()))))
    for match in SINGLE.finditer(text):
        h, mm, mark, h24, m24 = match.groups()
        word = h or h24
        found.append((match.group(0), one_time(text, word, mm or m24, mark, match.start())))
    return found


# "HH:MM" -> minutes after midnight.
def minutes_of(clock: str) -> int:
    hours, minutes = clock.split(":")
    return int(hours) * 60 + int(minutes)
