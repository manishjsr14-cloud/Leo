"""Tests for leo/language/turn_kind.py and the M2.3c rule in the graph (fake LLM, mock tools).

The examples are the test author's own and two M1.10 suite turns (L19, t09),
not the M2.3c check set.
"""

import pytest
from langchain_core.messages import HumanMessage
from pydantic import ValidationError

from leo.agents.productivity import run_agent as productivity_run
from leo.graph.responder import STATEMENT_NOTE, responder_messages
from leo.graph.supervisor import supervisor_node
from leo.language.turn_kind import turn_kind
from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.mock.productivity import mock_productivity_tools
from leo.tools.mock.research import mock_research_tools
from leo.tools.registry import by_name, tools_for_turn
from tests.graph_fakes import FakeChat

READS = {"get_events", "find_free_slots", "list_tasks", "list_notes", "calculate",
         "web_search", "read_page", "get_weather"}


@pytest.mark.parametrize("text, kind", [
    ("My sister lives in Nagpur.", "statement"),
    ("Office mein aaj bahut kaam tha.", "statement"),
    ("Kal Rahul ke saath meeting", "statement"),           # M1.10 t09
    ("Will it rain on Sunday?", "question"),
    ("Parso mera koi meeting hai?", "question"),
    ("Kitne baje hai doctor wala appointment", "question"),  # Hinglish question word
    ("Ek note likh lo: gas cylinder book karna hai", "request"),  # M1.10 L19
    ("Can you add eggs to my list?", "request"),            # a request wins over a question
    ("Start a timer for 5 minutes", "request"),
    ("Alarm laga do 6 baje ka", "request"),
    ("Move the gym session to Monday", "request"),
    ("Remind me to pay the rent", "request"),
])
def test_turn_kind(text, kind):
    assert turn_kind(text) == kind


# Exactly the tools that change nothing are marked read-only.
def test_read_only_tools():
    tools = by_name(mock_calendar_tools([]) + mock_productivity_tools([])
                    + mock_research_tools([]))
    assert {name for name, tool in tools.items() if tool.read_only} == READS


# A question keeps only the read-only tools; a request keeps them all.
def test_tools_for_turn():
    tools = by_name(mock_productivity_tools([]))
    assert set(tools_for_turn(tools, "question")) == {"list_tasks", "list_notes", "calculate"}
    assert tools_for_turn(tools, "request") is tools and tools_for_turn(tools, None) is tools


# A plain statement plans no agent and makes no LLM call.
def test_statement_runs_no_agent_and_no_llm_call():
    chat = FakeChat({"agents": ["productivity"], "task": "add it"})
    state = {"messages": [HumanMessage("I need to fix the bike.")], "hops": 0, "plan": []}
    update = supervisor_node(state, chat, ["productivity", "calendar"])
    assert update == {"agent_queue": [], "hops": 0, "turn_kind": "statement"}
    assert chat.calls == []


# On a question the agent is offered only read tools: a write reply fails the
# step schema, so it can never run, and the prompt lists no write tool.
def test_question_agent_never_runs_a_write():
    log = []
    tools = by_name(mock_productivity_tools(log))
    state = {"messages": [HumanMessage("Milk ka task hai kya?")], "plan": ["check tasks"],
             "agent_results": {}, "turn_kind": "question"}
    with pytest.raises(ValidationError):
        productivity_run(state, FakeChat({"add_task": {"title": "milk"}}), tools, 3)
    chat = FakeChat({"list_tasks": {}}, {"done": {"summary": "ok"}})
    productivity_run(state, chat, tools, 3)
    assert [c.tool for c in log] == ["list_tasks"]
    prompt = chat.calls[0]["messages"][0]["content"]
    assert "- list_tasks(" in prompt and "- add_task(" not in prompt  # the tool list


# After a statement the responder is told nothing was done: it may offer, never claim.
def test_statement_note_reaches_the_responder():
    said = responder_messages({"messages": [HumanMessage("x")], "turn_kind": "statement"})
    assert any(m["content"] == STATEMENT_NOTE for m in said)
    asked = responder_messages({"messages": [HumanMessage("x")], "turn_kind": "question"})
    assert not any(m["content"] == STATEMENT_NOTE for m in asked)
