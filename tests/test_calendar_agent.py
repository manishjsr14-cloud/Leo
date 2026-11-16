"""Tests for leo/agents/calendar.py and its guard, with a fake LLM and mock tools only."""

from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage

from leo.agents.calendar import calendar_agent, run_agent
from leo.agents.calendar_guard import ASK_TIME
from leo.config import load_config
from leo.graph.builder import build_graph
from leo.graph.responder import APPROVAL_NOTE, ASK_NOTE, tool_result_lines
from leo.language.calendar_words import ADD_OR_MOVE
from leo.language.time_spans import TWO_DAYS
from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.registry import by_name
from tests.graph_fakes import FakeChat

NOW = datetime(2026, 11, 16, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata"))  # Monday
CONFIG = load_config().calendar
DONE_WHEN = "Kal subah 10 baje Rahul ke saath meeting daal do"
TUE_10, TUE_11 = "2026-11-17T10:00:00+05:30", "2026-11-17T11:00:00+05:30"
MON = {"start": "2026-11-16T00:00:00+05:30", "end": "2026-11-17T00:00:00+05:30"}
MOVE_TO = {"start": "2026-11-16T17:00:00+05:30", "end": "2026-11-16T18:00:00+05:30"}
SAT_MORNING = {"start": "2026-11-21T06:00:00+05:30", "end": "2026-11-21T12:00:00+05:30"}


# A fresh call log and the mock calendar tools that write to it.
def fresh():
    log = []
    return log, by_name(mock_calendar_tools(log))


# Run the agent on one user message with the fixed "now".
def run(text: str, chat, tools, max_steps: int = 6) -> dict:
    state = {"messages": [HumanMessage(text)], "plan": [text], "agent_results": {}}
    return run_agent(state, chat, tools, max_steps, NOW, CONFIG)


# The done-when phrase creates the right mock event; the prompt shows the exact times.
def test_done_when_phrase_creates_the_right_event():
    log, tools = fresh()
    args = {"title": "Meeting with Rahul", "start": TUE_10, "end": TUE_11}
    chat = FakeChat({"create_event": args},
                    {"done": {"summary": "Added."}})
    out = run(DONE_WHEN, chat, tools)
    assert out["stopped"] == "done"
    assert [(c.tool, c.args) for c in log] == [("create_event", args)]
    prompt = chat.calls[0]["messages"][0]["content"]
    assert f"- Event: start {TUE_10}, end {TUE_11}" in prompt
    assert "never work out dates or times yourself" in prompt


# The model sends 11:00 when the parser said 10:00: refused, nothing logged.
def test_create_with_a_different_time_is_refused():
    log, tools = fresh()
    wrong = {"title": "Meeting with Rahul", "start": TUE_11,
             "end": "2026-11-17T12:00:00+05:30"}
    out = run(DONE_WHEN, FakeChat({"create_event": wrong},
                                  {"done": {"summary": "x"}}), tools)
    assert log == []
    assert TUE_10 in out["steps"][0]["result"]["error"]


# The model picks the 15:00 slot's neighbour (wrong event): refused, nothing logged.
def test_move_of_the_wrong_event_is_refused():
    log, tools = fresh()
    chat = FakeChat({"get_events": MON},
                    {"move_event": {"event_id": "mock-evt-gym", **MOVE_TO}},
                    {"done": {"summary": "x"}})
    out = run("3 baje wali meeting 5 baje kar do", chat, tools)
    assert [c.tool for c in log] == ["get_events"]
    assert "error" in out["steps"][1]["result"]


def test_move_of_the_right_event_runs():
    log, tools = fresh()
    chat = FakeChat({"get_events": MON},
                    {"move_event": {"event_id": "mock-evt-team", **MOVE_TO}},
                    {"done": {"summary": "Moved."}})
    run("3 baje wali meeting 5 baje kar do", chat, tools)
    assert [c.tool for c in log] == ["get_events", "move_event"]


# Two different day words in a move: the agent asks, with no LLM call.
def test_move_with_two_day_words_asks_without_llm():
    log, tools = fresh()
    chat = FakeChat({"done": {"summary": "x"}})
    out = run("kal ki 3 baje wali meeting parso 5 baje kar do", chat, tools)
    assert out == {"steps": [], "summary": TWO_DAYS, "stopped": "ask"}
    assert chat.calls == [] and log == []


# A create with a date but no time: the agent stops and the reply asks "kis time?".
def test_create_with_date_but_no_time_asks_for_the_time():
    log, tools = fresh()
    args = {"title": "Meet Rahul", "start": "2026-11-19T10:00:00+05:30",
            "end": "2026-11-19T11:00:00+05:30"}
    out = run("Thursday ko Rahul se milna hai", FakeChat({"create_event": args}),
              tools)
    assert (out["stopped"], out["summary"], log) == ("ask", ASK_TIME, [])
    assert f"- calendar: {ASK_NOTE}: {ASK_TIME}" in tool_result_lines({"calendar": out})


# A cancel is refused without approval; the responder is told it was not done.
def test_cancel_is_refused_and_responder_says_approval_needed():
    log, tools = fresh()
    sat = {"start": "2026-11-21T00:00:00+05:30", "end": "2026-11-22T00:00:00+05:30"}
    chat = FakeChat({"get_events": sat},
                    {"cancel_event": {"event_id": "mock-evt-gym"}},
                    {"done": {"summary": "Cancelled."}})
    out = run("Saturday ka gym cancel kar do", chat, tools)
    assert [c.tool for c in log] == ["get_events"]
    assert out["steps"][1]["result"]["needs_approval"] is True
    lines = tool_result_lines({"calendar": out})
    assert f'- calendar: cancel_event({{"event_id": "mock-evt-gym"}}) -> {APPROVAL_NOTE}.' in lines


# A range that is neither the window nor the whole day is refused.
def test_free_slots_range_must_come_from_the_words():
    log, tools = fresh()
    chat = FakeChat({"find_free_slots": {**SAT_MORNING}},
                    {"done": {"summary": "x"}})
    out = run("Thursday dopahar free hoon?", chat, tools)
    assert log == [] and "2026-11-19T12:00:00+05:30" in out["steps"][0]["result"]["error"]


# Through the graph: the supervisor lists calendar and routes to it.
def test_graph_routes_to_calendar_and_responder_sees_event():
    log, tools = fresh()
    args = {"title": "Meeting with Rahul", "start": TUE_10, "end": TUE_11}
    chat = FakeChat({"agents": ["calendar"], "task": "Add meeting with Rahul"},
                    {"create_event": args},
                    {"done": {"summary": "Added."}},
                    "Ho gaya! Kal 10 baje Rahul ke saath meeting daal di.")
    agents = {"calendar": calendar_agent(chat, tools, 6, CONFIG, now=lambda: NOW)}
    out = build_graph(chat, agents=agents).invoke(
        {"messages": [HumanMessage(DONE_WHEN)], "hops": 0, "plan": []})
    assert "- calendar: the user's own calendar" in chat.calls[0]["messages"][0]["content"]
    assert [c.tool for c in log] == ["create_event"]
    assert "mock-evt-1" in " ".join(m["content"] for m in chat.calls[-1]["messages"])
    assert out["messages"][-1].content.startswith("Ho gaya!")


# The tool names the first step's schema offered the model.
def offered(chat) -> set[str]:
    schema = chat.calls[0]["output_model"].model_json_schema()
    return {ref["$ref"].split("_", 1)[1] for ref in schema["anyOf"]}


# An "add" message never offers cancel_event or move_event (schema or prompt).
def test_add_message_never_offers_cancel_or_move():
    for text in (DONE_WHEN, "Add a dentist appointment on Thursday at 4:30 pm"):
        _, tools = fresh()
        chat = FakeChat(None)  # invalid reply: stops after step 1
        run(text, chat, tools)
        assert offered(chat) == {"get_events", "find_free_slots", "create_event"}
        assert "cancel_event(" not in chat.calls[0]["messages"][0]["content"]


def test_clear_message_offers_cancel_and_two_times_offer_move():
    _, tools = fresh()
    chat = FakeChat(None)  # invalid reply: stops after step 1
    run("Saturday subah clear kar do", chat, tools)
    assert "cancel_event" in offered(chat) and "move_event" not in offered(chat)
    chat = FakeChat(None)  # invalid reply: stops after step 1
    run("3 baje wali meeting 5 baje kar do", chat, tools)
    assert offered(chat) == {"get_events", "find_free_slots", "move_event"}  # no create


# An invented id is refused as such (before approval), and nothing is logged.
def test_cancel_of_an_id_not_listed_is_refused_before_approval():
    log, tools = fresh()
    chat = FakeChat({"cancel_event": {"event_id": "12345"}},
                    {"done": {"summary": "x"}})
    out = run("Saturday ka gym cancel kar do", chat, tools)
    result = out["steps"][0]["result"]
    assert "get_events first" in result["error"] and "needs_approval" not in result
    assert log == []


# Two times plus a create word: the agent asks, with no LLM call.
def test_two_times_with_a_create_word_asks():
    log, tools = fresh()
    chat = FakeChat(None)
    out = run("kal 3 baje se 5 baje tak workshop add karo", chat, tools)
    assert out == {"steps": [], "summary": ADD_OR_MOVE, "stopped": "ask"}
    assert chat.calls == [] and log == []
