"""Tests for leo/language/time_spans.py: two-time moves, day words and part-of-day windows."""

from datetime import datetime
from zoneinfo import ZoneInfo

from leo.config import load_config
from leo.language.clock import find_clocks
from leo.language.time_parser import split_words
from leo.language.time_spans import TOO_MANY_TIMES, TWO_DAYS, read_calendar_times

IST = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 11, 16, 9, 0, tzinfo=IST)  # Monday
CONFIG = load_config().calendar


# Read the calendar times with the fixed "now".
def read(text: str):
    return read_calendar_times(text, NOW, CONFIG)


# An IST datetime on a November 2026 day.
def at(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 11, day, hour, minute, tzinfo=IST)


def test_find_clocks_reads_every_time_once():
    assert find_clocks(split_words("sava teen baje wali meeting 5 baje")) == [
        (3, 15, "", 0), (5, 0, "", 5)]


def test_hinglish_move_first_time_is_current_second_is_new():
    times = read("3 baje wali meeting 5 baje kar do")
    assert (times.status, times.move_from, times.start) == ("ok", at(16, 15), at(16, 17))


def test_english_move_reads_the_same_way():
    times = read("Move my 3 pm meeting to 5 pm")
    assert (times.move_from, times.start) == (at(16, 15), at(16, 17))


def test_move_with_two_different_day_words_asks():
    times = read("kal ki 3 baje wali meeting parso 5 baje kar do")
    assert (times.status, times.question, times.start) == ("ask", TWO_DAYS, None)


def test_more_than_two_times_asks():
    assert read("3 baje, 4 baje ya 5 baje meeting rakh do").question == TOO_MANY_TIMES


def test_part_of_day_becomes_the_config_window():
    times = read("Thursday dopahar free hoon?")
    assert times.start is None
    assert times.window == (at(19, 12), at(19, 16))
    assert times.day == (at(19, 0), at(20, 0))


def test_evening_window_in_english():
    assert read("Am I free tomorrow evening?").window == (at(17, 16), at(17, 20))


def test_single_time_has_no_move_and_keeps_window():
    times = read("Kal subah 10 baje Rahul ke saath meeting daal do")
    assert (times.start, times.move_from) == (at(17, 10), None)
    assert times.window == (at(17, 6), at(17, 12))


def test_unclear_kal_asks_and_no_date_is_none():
    assert read("Kal Rahul ke saath meeting").status == "ask"
    assert read("hello Leo").status == "none"
