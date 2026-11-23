"""Tests for leo/agents/percent.py and the code-built "X% of Y" calculation (K05)."""

from langchain_core.messages import HumanMessage

from leo.agents.percent import percent_expression
from leo.agents.productivity import run_agent
from leo.tools.mock.productivity import mock_productivity_tools
from leo.tools.registry import by_name
from tests.graph_fakes import FakeChat


# Each phrase form gives the expression "X% of Y" from the message's own numbers.
def test_phrase_forms():
    for text, expected in (("What is 15% of 3200?", "15% of 3200"),
                           ("15 percent of 3,200", "15% of 3200"),
                           ("3200 ka 15% kitna hai?", "15% of 3200"),
                           ("2450 ke 18 percent batao", "18% of 2450"),
                           ("what's 12.5% of 80", "12.5% of 80")):
        assert percent_expression(text) == expected, text


# Other numbers, other maths or no percentage: left to the model.
def test_other_messages_give_none():
    for text in ("15% of 3200 plus 50", "What is 2 + 2?", "add milk to my tasks",
                 "15% kitna hai?", "dedh hazaar ka 10%"):
        assert percent_expression(text) is None, text


# Run the productivity agent on one message with mock tools.
def run(text: str, chat) -> tuple[dict, list]:
    log = []
    state = {"messages": [HumanMessage(text)], "plan": [text], "agent_results": {}}
    return run_agent(state, chat, by_name(mock_productivity_tools(log)), 4), log


# K05: calculated by code on the first attempt, with no LLM call.
def test_percent_is_calculated_by_code_without_the_model():
    chat = FakeChat(None)
    out, log = run("What is 15% of 3200?", chat)
    assert chat.calls == [] and out["stopped"] == "done"
    assert [(c.tool, c.args) for c in log] == [("calculate", {"expression": "15% of 3200"})]
    assert out["steps"][0]["result"]["result"] == "480"


# With a second request ("and ..."), the model handles the message as before.
def test_linked_request_goes_to_the_model():
    chat = FakeChat({"calculate": {"expression": "15% of 3200"}}, {"done": {"summary": "ok"}})
    run("What is 15% of 3200 and add milk to my tasks", chat)
    assert len(chat.calls) >= 1
