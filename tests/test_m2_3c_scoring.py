"""Tests for evals/m2_3c_scoring.py: counts come from the mock tools' log only."""

from evals import m2_3c_scoring as sc

DATA = {"statements": [{"id": "S1"}], "questions": [{"id": "Q1"}],
        "requests": [{"id": "W1", "expect_write": "add_task"}]}


# A record with this tool log and these agents.
def rec(log: list[dict], agents: list[str] | None = None) -> dict:
    return {"tool_log": log, "agents": agents or []}


# One logged call.
def call(tool: str, result=None) -> dict:
    return {"tool": tool, "args": {}, "result": {} if result is None else result}


# Writes are exactly the tools not marked read-only.
def test_writes():
    assert sc.WRITES == {"create_event", "move_event", "cancel_event", "add_task",
                         "complete_task", "add_note", "start_timer"}


# Every part met: no statement call, reads only for the question, the write ran.
def test_all_parts_met():
    records = {"S1": rec([]), "Q1": rec([call("get_events")], ["calendar"]),
               "W1": rec([call("add_task")], ["productivity"]), "t09": rec([])}
    assert all(ok for _, ok in sc.parts(DATA, records))


# Any statement call, a question's write, a failed write or a t09 agent misses its part.
def test_each_part_can_miss():
    records = {"S1": rec([call("list_tasks")]), "Q1": rec([call("add_note")]),
               "W1": rec([call("add_task", {"error": "no title"})]),
               "t09": rec([], ["calendar"])}
    assert [ok for _, ok in sc.parts(DATA, records)] == [False, False, False, False]
