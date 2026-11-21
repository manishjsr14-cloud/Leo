"""Tests for the repeated-call guard in leo/agents/loop.py (fake LLM)."""

from langchain_core.messages import HumanMessage

from leo.agents.productivity import run_agent
from leo.memory.store import open_db
from leo.tools.mock.productivity import mock_productivity_tools
from leo.tools.real.productivity import real_productivity_tools
from leo.tools.registry import by_name
from tests.graph_fakes import FakeChat


# A fresh call log and the mock productivity tools that write to it.
def fresh():
    log = []
    return log, by_name(mock_productivity_tools(log))


# State for one user message, as the supervisor leaves it.
def state_for(text: str, task: str) -> dict:
    return {"messages": [HumanMessage(text)], "plan": [task], "agent_results": {}}


# A model that repeats a successful add_task leaves exactly one task in the
# database: the repeat is refused and the run ends.
def test_repeated_successful_call_is_refused_and_ends_the_run(tmp_path):
    conn = open_db(tmp_path / "leo.db")
    tools = by_name(real_productivity_tools(conn))
    chat = FakeChat({"add_task": {"title": "milk"}})  # repeats forever
    # "and" links two requests, so the run does not end in code after one add.
    out = run_agent(state_for("add milk and eggs to my tasks", "add milk"), chat, tools, 4)
    titles = [r["title"] for r in conn.execute("SELECT title FROM tasks")]
    conn.close()
    assert titles == ["milk"]
    assert out["stopped"] == "repeated_call" and len(out["steps"]) == 1
    assert len(chat.calls) == 2


# A failed call may be tried again (the model can fix its arguments).
def test_a_failed_call_is_not_counted_as_done():
    log, tools = fresh()
    chat = FakeChat({"complete_task": {"task_id": 99}})
    out = run_agent(state_for("complete task 99", "complete"), chat, tools, 3)
    assert out["stopped"] == "max_steps" and len(log) == 3
