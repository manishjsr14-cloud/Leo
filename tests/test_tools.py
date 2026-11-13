"""Tests for the tool layer: tiers, argument checks, approval and the mock call log."""

import pytest
from pydantic import ValidationError

from leo.tools.base import Tier, ToolArgs
from leo.tools.mock.calendar import CREATED_EVENT_ID, FIXED_EVENTS
from leo.tools.registry import (
    ApprovalRequiredError,
    UnknownToolError,
    by_name,
    call_tool,
    mock_tools,
)

SAT_8 = "2026-11-14T08:00:00+05:30"
SAT_9 = "2026-11-14T09:00:00+05:30"
RANGE = {"start": SAT_8, "end": SAT_9}


# A fresh call log and the mock tools that write to it.
def fresh():
    log = []
    return log, mock_tools(log)


def test_every_tool_is_complete_and_names_unique():
    _, tools = fresh()
    assert len(tools) == 3
    for name, tool in tools.items():
        assert tool.name == name
        assert tool.description
        assert isinstance(tool.tier, Tier)
        assert issubclass(tool.args_model, ToolArgs)
    duplicate = list(tools.values()) + [tools["get_events"]]
    with pytest.raises(ValueError, match="duplicate"):
        by_name(duplicate)


def test_tiers_match_section_9():
    _, tools = fresh()
    assert tools["get_events"].tier is Tier.SAFE
    assert tools["create_event"].tier is Tier.NOTIFY
    assert tools["cancel_event"].tier is Tier.CONFIRM


def test_get_events_returns_fixed_data_and_logs_each_call():
    log, tools = fresh()
    first = call_tool(tools, "get_events", RANGE)
    first[0]["title"] = "changed by caller"
    second = call_tool(tools, "get_events", RANGE)
    assert second == FIXED_EVENTS
    assert [c.tool for c in log] == ["get_events", "get_events"]
    assert log[1].args == RANGE
    assert log[1].result == FIXED_EVENTS


def test_create_event_returns_fixed_id_and_logs_args():
    log, tools = fresh()
    args = {"title": "Lonavala trip", **RANGE}
    event = call_tool(tools, "create_event", args)
    assert event == {"id": CREATED_EVENT_ID, **args}
    assert len(log) == 1
    assert log[0].tool == "create_event"
    assert log[0].args == args


@pytest.mark.parametrize(
    "args",
    [
        RANGE,  # missing title
        {"title": "", **RANGE},  # empty title
        {"title": "Gym", "start": "2026-11-14T08:00:00", "end": SAT_9},  # no time zone
        {"title": "Gym", "start": SAT_9, "end": SAT_8},  # end before start
    ],
)
def test_bad_args_are_rejected_and_not_logged(args):
    log, tools = fresh()
    with pytest.raises(ValidationError):
        call_tool(tools, "create_event", args)
    assert log == []


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("get_events", {**RANGE, "limit": 5}),
        ("create_event", {"title": "Gym", **RANGE, "titel": "typo"}),
        ("cancel_event", {"event_id": "mock-evt-gym", "force": True}),
    ],
)
def test_unknown_keys_are_rejected(name, args):
    log, tools = fresh()
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        call_tool(tools, name, args, approved=True)
    assert log == []


def test_red_tool_without_approval_is_refused():
    log, tools = fresh()
    with pytest.raises(ApprovalRequiredError):
        call_tool(tools, "cancel_event", {"event_id": "mock-evt-gym"})
    assert log == []


def test_red_tool_with_approval_runs_and_is_logged():
    log, tools = fresh()
    result = call_tool(tools, "cancel_event", {"event_id": "mock-evt-gym"}, approved=True)
    assert result == {"cancelled": "mock-evt-gym"}
    assert [c.tool for c in log] == ["cancel_event"]


def test_approval_inside_model_args_is_ignored():
    log, tools = fresh()
    args = {"event_id": "mock-evt-gym", "approved": True}
    with pytest.raises(ValidationError, match="approved"):
        call_tool(tools, "cancel_event", args, approved=False)
    assert log == []


def test_approved_must_be_exactly_true():
    log, tools = fresh()
    with pytest.raises(ApprovalRequiredError):
        call_tool(tools, "cancel_event", {"event_id": "mock-evt-gym"}, approved="yes")
    assert log == []


def test_unknown_tool_name_is_a_clear_error():
    log, tools = fresh()
    with pytest.raises(UnknownToolError, match="delete_everything"):
        call_tool(tools, "delete_everything", {})
    assert log == []


def test_separate_logs_do_not_share_calls():
    log_a, tools_a = fresh()
    log_b, _ = fresh()
    call_tool(tools_a, "get_events", RANGE)
    assert len(log_a) == 1
    assert log_b == []
