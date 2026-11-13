"""Tests for the responder rule: only successful tool results reach the reply."""

from langchain_core.messages import HumanMessage

from leo.graph.responder import NO_ACTION_NOTE, responder_node
from tests.graph_fakes import FakeChat

ASK = {"messages": [HumanMessage("what is 18% of 2450")]}


# Everything the responder sent to the LLM after its fixed system prompt
# (which itself mentions the note), as one string.
def sent(chat: FakeChat) -> str:
    return " ".join(m["content"] for m in chat.calls[0]["messages"][1:])


# (a) An agent ran but no tool call succeeded: the note is added, and the
# agent's own summary (LLM text) is not passed on.
def test_no_successful_tool_call_adds_the_note():
    failed = {"tool": "calculate", "args": {"expression": "x"}, "result": {"error": "bad"}}
    outcome = {"steps": [failed], "summary": "18% of 2450 is 441.", "stopped": "done"}
    chat = FakeChat("Sorry, that was not done.")
    responder_node({**ASK, "agent_results": {"productivity": outcome}}, chat)
    text = sent(chat)
    assert f"productivity: {NO_ACTION_NOTE}." in text
    assert "441" not in text


# An agent that ran no tool at all also gets the note.
def test_agent_with_no_steps_gets_the_note():
    outcome = {"steps": [], "summary": "", "stopped": "invalid_output"}
    chat = FakeChat("Sorry.")
    responder_node({**ASK, "agent_results": {"productivity": outcome}}, chat)
    assert NO_ACTION_NOTE in sent(chat)


# (b) A successful calculate result of 441 reaches the responder.
def test_successful_calculate_passes_441():
    result = {"expression": "18% of 2450", "computed": "(18/100)*2450", "result": "441"}
    step = {"tool": "calculate", "args": {"expression": "18% of 2450"}, "result": result}
    outcome = {"steps": [step], "summary": "", "stopped": "done"}
    chat = FakeChat("18% of 2450 is 441.")
    responder_node({**ASK, "agent_results": {"productivity": outcome}}, chat)
    text = sent(chat)
    assert '"result": "441"' in text
    assert NO_ACTION_NOTE not in text


# Only failed steps are dropped: a good step after a failed one is kept.
def test_failed_steps_are_dropped_and_good_ones_kept():
    bad = {"tool": "complete_task", "args": {"task_id": 9}, "result": {"error": "no task"}}
    good = {"tool": "complete_task", "args": {"task_id": 1},
            "result": {"id": 1, "title": "milk", "done": True}}
    chat = FakeChat("Done.")
    responder_node({**ASK, "agent_results": {"productivity": {"steps": [bad, good]}}}, chat)
    text = sent(chat)
    assert "no task" not in text and '"title": "milk"' in text
    assert NO_ACTION_NOTE not in text


# A plain chat turn (no agent ran) has no tool results and no note.
def test_plain_chat_has_no_note():
    chat = FakeChat("Hi!")
    responder_node({"messages": [HumanMessage("hi")]}, chat)
    assert "Tool results" not in sent(chat)
