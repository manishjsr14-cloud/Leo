"""Tests for leo/graph/result_words.py and leo/language/say_time.py."""

from leo.graph.result_words import result_in_words
from leo.language.say_time import say_iso_span


def test_move_result_in_words():
    moved = {"id": "mock-evt-team", "title": "Team meeting",
             "start": "2026-11-16T17:00:00+05:30", "end": "2026-11-16T18:00:00+05:30"}
    assert result_in_words("move_event", moved) == \
        "Moved 'Team meeting' to Mon 16 Nov, 5:00-6:00 pm"


def test_spans_across_noon_and_whole_days():
    assert say_iso_span("2026-11-19T11:00:00+05:30", "2026-11-19T13:00:00+05:30") == \
        "Thu 19 Nov, 11:00 am-1:00 pm"
    assert say_iso_span("2026-11-21T00:00:00+05:30", "2026-11-22T00:00:00+05:30") == \
        "Sat 21 Nov (whole day)"
    assert say_iso_span("2026-11-16T00:00:00+05:30", "2026-11-23T00:00:00+05:30") == \
        "Mon 16 Nov to Sun 22 Nov"


def test_events_free_slots_and_unknown_shapes():
    events = [{"id": "g", "title": "Gym", "start": "2026-11-21T08:00:00+05:30",
               "end": "2026-11-21T09:00:00+05:30"}]
    assert result_in_words("get_events", events) == "1 event(s): 'Gym', Sat 21 Nov, 8:00-9:00 am"
    assert result_in_words("get_events", []) == "No events in that time"
    assert result_in_words("find_free_slots", [{"start": "2026-11-19T12:00:00+05:30",
                                                "end": "2026-11-19T13:00:00+05:30"}]) == \
        "Free: Thu 19 Nov, 12:00-1:00 pm"
    assert result_in_words("move_event", {"oops": 1}) is None
    assert result_in_words("unknown_tool", {}) is None
