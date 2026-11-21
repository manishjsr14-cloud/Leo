"""Tests for leo/language/time_parser.py, one rule at a time.

Uses its own "now" (Wednesday 2026-11-18 11:00 IST) and its own phrases; the
frozen phrase set (evals/scenarios/m1_6_indian_phrases.yaml) is scored separately.
"""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from leo.language.time_parser import current_time, parse_time

IST = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 11, 18, 11, 0, tzinfo=IST)            # a Wednesday


# Shorthand: parse with NOW (or another hour on the same day).
def parse(text: str, hour: int = 11, minute: int = 0):
    return parse_time(text, NOW.replace(hour=hour, minute=minute))


@pytest.mark.parametrize(
    ("text", "day", "clock", "assumed"),
    [
        ("kal subah 9 baje milenge", 19, "09:00", False),   # future ending -enge
        ("parso raat 10 baje", 20, "22:00", False),
        ("parso raat 1 baje", 21, "01:00", False),           # raat 12-4: next morning
        ("aaj sava chaar baje", 18, "16:15", True),          # sava +15 min, default pm
        ("aaj paune ek baje", 18, "12:45", True),            # paune -15 min
        ("aaj dhai baje", 18, "14:30", True),
        ("aaj 8 baje", 18, "08:00", True),                   # 8-11 default am; aaj is literal
        ("aaj 9:15 am", 18, "09:15", False),
        ("aaj 18:30", 18, "18:30", False),                   # 24-hour clock needs no default
        ("dopahar 12 baje", 18, "12:00", False),             # no day word, still ahead
        ("subah 10 baje", 19, "10:00", False),               # no day word, passed -> tomorrow
        ("Thursday 7 pm", 19, "19:00", False),
        ("agle Tuesday subah 6 baje", 24, "06:00", False),   # next week, not this week
        ("teen ghante baad", 18, "14:00", False),            # relative from now
        ("in 45 minutes", 18, "11:45", False),
        ("after 2 hours", 18, "13:00", False),
        ("dentist tomorrow at 4", 19, "16:00", True),       # "at <hour>": default pm, assumed
        ("call Riya on Friday at 9", 20, "09:00", True),    # 8-11 default am, assumed
        ("lunch tomorrow at 12", 19, "12:00", True),
        ("tomorrow at 4 pm", 19, "16:00", False),           # am/pm given: not assumed
        ("tomorrow at 17", 19, "17:00", False),             # 24-hour clock: not assumed
    ],
)
# Each rule gives the expected IST date, time and assumed_ampm flag.
def test_ok(text, day, clock, assumed):
    result = parse(text)
    assert result.status == "ok"
    assert result.date == date(2026, 11, day)
    assert result.time == time.fromisoformat(clock)
    assert result.assumed_ampm is assumed


# "kal" with a past signal is yesterday; no time stays None.
def test_kal_past():
    result = parse("kal shaam call hua tha")
    assert (result.status, result.date, result.time) == ("ok", date(2026, 11, 17), None)


@pytest.mark.parametrize(
    ("text", "hour", "reason"),
    [
        ("kal dopahar 2 baje", 11, "kal"),                  # no tense signal
        ("kal gaya tha aur kal jaana hai", 11, "kal"),      # both signals
        ("tomorrow ya yesterday", 11, "kal"),               # both words
        ("kal", 2, "midnight"),                              # 00:00-04:00
        ("tomorrow 5 pm", 0, "midnight"),
        ("parso", 3, "midnight"),
        ("day after tomorrow", 1, "midnight"),
        ("budhvaar ko", 11, "weekday"),                      # today is Wednesday
        ("next Wednesday", 11, "weekday"),
        ("agle Sunday", 11, "weekday"),                      # still in this week
    ],
)
# Two likely meanings give ask, with the reason and a question for the user.
def test_ask(text, hour, reason):
    result = parse(text, hour)
    assert (result.status, result.ask_about) == ("ask", reason)
    assert result.question
    assert result.date is None and result.time is None


# From 04:00 the midnight rule no longer applies; "aaj" is always literal.
def test_midnight_edges():
    assert parse("kal subah 9 baje meeting hai", 4).date == date(2026, 11, 19)
    early = parse("aaj 5 pm", 2)
    assert (early.date, early.time) == (date(2026, 11, 18), time(17, 0))


# "pehle"/"before" gives a reminder offset, not the event time.
def test_reminder_offset():
    result = parse("kal 4 pm meeting hai, 10 minute pehle yaad dila")
    assert (result.date, result.time, result.remind_before_min) == (
        date(2026, 11, 19), time(16, 0), 10)
    wedding = parse("shanivaar ko shaadi hai, do din pehle bata dena")
    assert (wedding.date, wedding.time, wedding.remind_before_min) == (
        date(2026, 11, 21), None, 2880)


@pytest.mark.parametrize("text", ["", "kabhi bhi", "thodi der baad", "meeting daal do"])
# Text with no day, weekday, clock time or duration is not understood.
def test_not_understood(text):
    assert parse(text).status == "not_understood"


# A "now" in another zone is converted to IST first: 20:00 UTC is 01:30 IST.
def test_other_zone_now_is_converted():
    utc_now = datetime(2026, 11, 17, 20, 0, tzinfo=UTC)
    assert parse_time("kal", utc_now).ask_about == "midnight"


# A naive "now" is taken as IST.
def test_naive_now_is_ist():
    result = parse_time("aaj 5 pm", datetime(2026, 11, 18, 11, 0))
    assert result.date == date(2026, 11, 18)


# Without "now", the parser uses the current IST time from config.
def test_default_now_is_ist():
    assert current_time().utcoffset() == timedelta(hours=5, minutes=30)
    assert parse_time("in 1 hour").status == "ok"


@pytest.mark.parametrize(
    ("text", "day", "clock"),
    [
        ("an hour baad yaad dilana", 18, "12:00"),           # "an" = 1
        ("remind me in a minute", 18, "11:01"),              # "a" = 1
        ("in a day", 19, "11:00"),
        ("half an hour mein nikalna hai", 18, "11:30"),      # "half an" = 1/2
        ("in half an hour", 18, "11:30"),
        ("sava do ghante baad", 18, "13:15"),                # modifier + number before unit
    ],
)
# "a"/"an" before a unit count as 1, "half an" as 1/2, from now.
def test_a_an_half_an(text, day, clock):
    result = parse(text)
    assert (result.status, result.date, result.time) == (
        "ok", date(2026, 11, day), time.fromisoformat(clock))


# "a"/"an" also work in reminder offsets.
def test_a_an_offset():
    result = parse("parso 9 am interview, an hour before remind karna")
    assert (result.date, result.time, result.remind_before_min) == (
        date(2026, 11, 20), time(9, 0), 60)
    assert parse("kal 5 pm call hai, half an hour pehle bata dena").remind_before_min == 30


# "at" before a duration or a non-hour number is not a clock time.
def test_at_without_an_hour_is_not_a_clock():
    assert parse("remind me in 10 minutes").time == time(11, 10)
    assert parse("tomorrow at 30").time is None
    assert parse("tomorrow at 2.5").time is None
