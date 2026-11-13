"""Tests for the productivity tools: real ones on a temporary SQLite file, and mocks."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from leo.memory.store import open_db
from leo.tools.base import Tier, ToolError
from leo.tools.mock.productivity import FIXED_TASKS, mock_productivity_tools
from leo.tools.real.productivity import real_productivity_tools
from leo.tools.registry import by_name, call_tool

NOW = datetime.fromisoformat("2026-11-13T18:00:00+05:30")
NAMES = {"add_task", "list_tasks", "complete_task", "add_note", "list_notes",
         "start_timer", "calculate"}


# Real tools on a fresh temporary database; `rings` collects timer schedules.
@pytest.fixture
def real(tmp_path):
    rings = []
    conn = open_db(tmp_path / "leo.db")
    tools = by_name(real_productivity_tools(
        conn, schedule=lambda s, label: rings.append((s, label)), now=lambda: NOW))
    yield tools, conn, rings
    conn.close()


def test_seven_safe_tools_in_real_and_mock(real):
    tools, _, _ = real
    mocks = by_name(mock_productivity_tools([]))
    assert set(tools) == set(mocks) == NAMES
    assert all(t.tier is Tier.SAFE for t in [*tools.values(), *mocks.values()])


def test_add_then_list_tasks(real):
    tools, conn, _ = real
    assert call_tool(tools, "add_task", {"title": "milk"}) == {
        "id": 1, "title": "milk", "done": False}
    call_tool(tools, "add_task", {"title": "eggs"})
    assert [t["title"] for t in call_tool(tools, "list_tasks", {})] == ["milk", "eggs"]
    row = conn.execute("SELECT created_at FROM tasks WHERE id = 1").fetchone()
    assert row["created_at"] == NOW.isoformat()


def test_complete_task_hides_it_from_default_list(real):
    tools, _, _ = real
    call_tool(tools, "add_task", {"title": "milk"})
    call_tool(tools, "add_task", {"title": "eggs"})
    assert call_tool(tools, "complete_task", {"task_id": 1}) == {
        "id": 1, "title": "milk", "done": True}
    assert [t["title"] for t in call_tool(tools, "list_tasks", {})] == ["eggs"]
    everything = call_tool(tools, "list_tasks", {"include_done": True})
    assert [t["done"] for t in everything] == [True, False]


def test_complete_unknown_task_is_a_tool_error(real):
    tools, _, _ = real
    with pytest.raises(ToolError, match="no task with id 9"):
        call_tool(tools, "complete_task", {"task_id": 9})


def test_notes_newest_first_with_limit(real):
    tools, _, _ = real
    for text in ["first", "second", "third"]:
        call_tool(tools, "add_note", {"text": text})
    notes = call_tool(tools, "list_notes", {"limit": 2})
    assert [n["text"] for n in notes] == ["third", "second"]


def test_timer_returns_end_time_and_schedules_ring(real):
    tools, _, rings = real
    out = call_tool(tools, "start_timer", {"minutes": 10, "label": "chai"})
    assert out == {"label": "chai", "minutes": 10, "ends_at": "2026-11-13T18:10:00+05:30"}
    assert rings == [(600, "chai")]


def test_calculate_uses_sympy_and_bad_input_is_tool_error(real):
    tools, _, _ = real
    assert call_tool(tools, "calculate", {"expression": "18% of 2450"})["result"] == "441"
    with pytest.raises(ToolError):
        call_tool(tools, "calculate", {"expression": "__import__('os')"})


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("add_task", {"title": ""}),
        ("add_task", {"title": "milk", "priority": "high"}),
        ("complete_task", {"task_id": 0}),
        ("start_timer", {"minutes": 0}),
        ("start_timer", {"minutes": 2000}),
        ("list_notes", {"limit": 500}),
    ],
)
def test_bad_args_are_rejected(real, name, args):
    tools, conn, _ = real
    with pytest.raises(ValidationError):
        call_tool(tools, name, args)
    assert conn.execute("SELECT count(*) FROM tasks").fetchone()[0] == 0


def test_mocks_return_fixed_data_and_log_calls_and_errors():
    log = []
    tools = by_name(mock_productivity_tools(log))
    assert call_tool(tools, "list_tasks", {}) == FIXED_TASKS
    assert call_tool(tools, "complete_task", {"task_id": 1})["done"] is True
    with pytest.raises(ToolError):
        call_tool(tools, "complete_task", {"task_id": 99})
    assert [c.tool for c in log] == ["list_tasks", "complete_task", "complete_task"]
    assert log[2].result == {"error": "no task with id 99; use list_tasks for ids"}


# Add one task per title, in order (ids 1, 2, 3, ...).
def add_all(tools, *titles):
    for title in titles:
        call_tool(tools, "add_task", {"title": title})


# The whole tasks table as (id, title, done) rows.
def table(conn):
    return [tuple(r) for r in conn.execute("SELECT id, title, done FROM tasks ORDER BY id")]


def test_complete_by_title_one_match_marks_it_done(real):
    tools, conn, _ = real
    add_all(tools, "Buy Milk", "eggs")
    assert call_tool(tools, "complete_task", {"title": "milk"}) == {
        "id": 1, "title": "Buy Milk", "done": True}
    assert table(conn) == [(1, "Buy Milk", 1), (2, "eggs", 0)]


def test_complete_by_title_two_matches_lists_both_and_changes_nothing(real):
    tools, conn, _ = real
    add_all(tools, "milk", "eggs", "Milk for chai")
    with pytest.raises(ToolError) as error:
        call_tool(tools, "complete_task", {"title": "milk"})
    message = str(error.value)
    assert "2 open tasks match 'milk'" in message
    assert "'id': 1" in message and "'id': 3" in message and "'id': 2" not in message
    assert table(conn) == [(1, "milk", 0), (2, "eggs", 0), (3, "Milk for chai", 0)]


def test_complete_by_title_no_match_changes_nothing(real):
    tools, conn, _ = real
    add_all(tools, "eggs")
    with pytest.raises(ToolError, match="no open task matches 'milk'"):
        call_tool(tools, "complete_task", {"title": "milk"})
    assert table(conn) == [(1, "eggs", 0)]


@pytest.mark.parametrize("args", [{"task_id": 1, "title": "milk"}, {}])
def test_complete_needs_exactly_one_of_id_or_title(real, args):
    tools, conn, _ = real
    add_all(tools, "milk")
    with pytest.raises(ValidationError, match="exactly one of task_id or title"):
        call_tool(tools, "complete_task", args)
    assert table(conn) == [(1, "milk", 0)]


@pytest.mark.parametrize("args", [{"task_id": 1}, {"title": "milk"}])
def test_completing_an_already_done_task_is_an_error(real, args):
    tools, conn, _ = real
    add_all(tools, "milk")
    call_tool(tools, "complete_task", {"task_id": 1})
    done_at = conn.execute("SELECT done_at FROM tasks WHERE id = 1").fetchone()[0]
    with pytest.raises(ToolError, match="already done"):
        call_tool(tools, "complete_task", args)
    assert conn.execute("SELECT done_at FROM tasks WHERE id = 1").fetchone()[0] == done_at
