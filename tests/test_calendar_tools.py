"""Tests for the M1.7 mock calendar tools: free slots, move, tiers and the call log."""

import pytest
from pydantic import ValidationError

from leo.tools.base import Tier, ToolError
from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.mock.research import mock_research_tools
from leo.tools.registry import by_name, call_tool

THU_12 = "2026-11-19T12:00:00+05:30"
THU_16 = "2026-11-19T16:00:00+05:30"


# A fresh call log and the mock calendar tools that write to it.
def fresh(events=None):
    log = []
    return log, by_name(mock_calendar_tools(log, events))


def test_tiers_match_section_9():
    _, tools = fresh()
    tiers = {name: tool.tier for name, tool in tools.items()}
    assert tiers == {"get_events": Tier.SAFE, "find_free_slots": Tier.SAFE,
                     "create_event": Tier.NOTIFY, "move_event": Tier.NOTIFY,
                     "cancel_event": Tier.CONFIRM}


# Thursday afternoon has lunch 13-14, so the free time is 12-13 and 14-16.
def test_free_slots_are_the_gaps_around_events():
    log, tools = fresh()
    slots = call_tool(tools, "find_free_slots", {"start": THU_12, "end": THU_16})
    assert slots == [
        {"start": THU_12, "end": "2026-11-19T13:00:00+05:30"},
        {"start": "2026-11-19T14:00:00+05:30", "end": THU_16},
    ]
    assert [c.tool for c in log] == ["find_free_slots"]


def test_free_slots_with_no_events_is_the_whole_range():
    _, tools = fresh()
    start, end = "2026-11-17T16:00:00+05:30", "2026-11-17T20:00:00+05:30"
    assert call_tool(tools, "find_free_slots", {"start": start, "end": end}) == [
        {"start": start, "end": end}]


def test_move_known_event_returns_new_times_and_logs():
    log, tools = fresh()
    args = {"event_id": "mock-evt-team", "start": "2026-11-16T17:00:00+05:30",
            "end": "2026-11-16T18:00:00+05:30"}
    moved = call_tool(tools, "move_event", args)
    assert moved == {"id": "mock-evt-team", "title": "Team meeting",
                     "start": args["start"], "end": args["end"]}
    assert [(c.tool, c.args) for c in log] == [("move_event", args)]


def test_move_unknown_event_is_an_error_and_not_logged():
    log, tools = fresh()
    with pytest.raises(ToolError, match="no event"):
        call_tool(tools, "move_event", {"event_id": "nope", "start": THU_12, "end": THU_16})
    assert log == []


def test_move_end_must_be_after_start():
    _, tools = fresh()
    with pytest.raises(ValidationError):
        call_tool(tools, "move_event", {"event_id": "mock-evt-team",
                                        "start": THU_16, "end": THU_12})


def test_given_events_and_weather_days_replace_the_fixed_ones():
    events = [{"id": "e1", "title": "X", "start": THU_12, "end": THU_16}]
    _, tools = fresh(events)
    assert call_tool(tools, "get_events", {"start": THU_12, "end": THU_16}) == events
    days = [{"date": "2026-11-21", "day": "Saturday", "rain_chance_pct": 5, "rain_mm": 0.0}]
    weather = by_name(mock_research_tools([], days))
    assert call_tool(weather, "get_weather", {"place": "Lonavala"})["days"] == days
