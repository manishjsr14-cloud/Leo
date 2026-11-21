"""Tests for the calculate check: numbers must come from the user's message (M1.8)."""

import pytest
from langchain_core.messages import HumanMessage

from leo.agents.calculate_guard import foreign_numbers, guard_calculate
from leo.agents.productivity import run_agent
from leo.tools.base import ToolError
from leo.tools.mock.productivity import mock_productivity_tools
from leo.tools.registry import by_name, call_tool
from tests.graph_fakes import FakeChat


def test_numbers_copied_from_the_message_pass():
    assert foreign_numbers("18% of 2450", "what is 18% of 2450") == []
    assert foreign_numbers("(18/100)*2450", "2450 ka 18 percent kitna hai?") == []


def test_numbers_in_words_pass():
    assert foreign_numbers("10% of 1500", "dedh hazaar ka 10%") == []


def test_a_miscopied_number_is_refused():
    assert foreign_numbers("15% of 320-0", "What is 15% of 3200?") == ["320", "0"]
    assert foreign_numbers("100 + 5", "what is 7 + 5") == ["100"]  # no % in the message


def test_the_check_refuses_before_the_calculator_runs():
    log = []
    tools = guard_calculate(by_name(mock_productivity_tools(log)), "What is 15% of 3200?")
    with pytest.raises(ToolError, match="not in the user's message"):
        call_tool(tools, "calculate", {"expression": "15% of 320-0"})
    assert call_tool(tools, "calculate", {"expression": "15% of 3200"})["result"] == "480"


def test_agent_sees_the_refusal_and_tries_again():
    log = []
    chat = FakeChat({"calculate": {"expression": "15% of 320-0"}},
                    {"calculate": {"expression": "15% of 3200"}})
    state = {"messages": [HumanMessage("What is 15% of 3200?")], "plan": ["x"],
             "agent_results": {}}
    out = run_agent(state, chat, by_name(mock_productivity_tools(log)), 4)
    assert "error" in out["steps"][0]["result"]
    assert out["steps"][1]["result"]["result"] == "480" and out["stopped"] == "done"
