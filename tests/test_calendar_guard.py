"""Tests for leo/agents/calendar_guard.py, the second check behind the code-filled
times: a full call with other times or ranges is refused and nothing is logged."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from leo.agents.calendar_fill import named_ranges
from leo.agents.calendar_guard import guard_calendar_tools
from leo.config import load_config
from leo.language.time_spans import read_calendar_times
from leo.tools.base import ToolError
from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.registry import by_name, call_tool

NOW = datetime(2026, 11, 16, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata"))  # Monday
CONFIG = load_config().calendar


# Guarded mock tools and their log for one user message.
def guarded(text: str):
    log = []
    times = read_calendar_times(text, NOW, CONFIG)
    tools = guard_calendar_tools(by_name(mock_calendar_tools(log)), times,
                                 CONFIG.default_event_minutes, named_ranges(times, NOW))
    return log, tools


# A full create_event at 11:00 when the parser said 10:00: refused, nothing logged.
def test_create_with_a_different_time_is_refused():
    log, tools = guarded("Kal subah 10 baje Rahul ke saath meeting daal do")
    with pytest.raises(ToolError, match="2026-11-17T10:00:00"):
        call_tool(tools, "create_event", {"title": "Meeting with Rahul",
                                          "start": "2026-11-17T11:00:00+05:30",
                                          "end": "2026-11-17T12:00:00+05:30"})
    assert log == []


# A range that is none of the named ranges is refused.
def test_range_not_offered_is_refused():
    log, tools = guarded("Thursday dopahar free hoon?")
    with pytest.raises(ToolError, match="2026-11-19T12:00:00"):
        call_tool(tools, "find_free_slots", {"start": "2026-11-21T06:00:00+05:30",
                                             "end": "2026-11-21T12:00:00+05:30"})
    assert log == []


# An invented id is refused as such (before approval), and nothing is logged.
def test_cancel_of_an_id_not_listed_is_refused_before_approval():
    log, tools = guarded("Saturday ka gym cancel kar do")
    with pytest.raises(ToolError, match="get_events first"):
        call_tool(tools, "cancel_event", {"event_id": "12345"})
    assert log == []
