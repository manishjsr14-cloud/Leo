"""Tests for leo/agents/calendar.py, with a fake LLM and mock tools only.
The model gives only a title, an event id or a range name; code fills in times."""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage

from leo.agents.calendar import calendar_agent, run_agent
from leo.agents.calendar_guard import ASK_TIME
from leo.config import load_config
from leo.graph.builder import build_graph
from leo.graph.responder import fact_lines
from leo.language.calendar_words import ADD_OR_MOVE
from leo.language.time_spans import TWO_DAYS
from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.registry import by_name
from tests.graph_fakes import FakeChat

NOW = datetime(2026, 11, 16, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata"))  # Monday
CONFIG = load_config().calendar
DONE_WHEN = "Kal subah 10 baje Rahul ke saath meeting daal do"
TUE_10, TUE_11 = "2026-11-17T10:00:00+05:30", "2026-11-17T11:00:00+05:30"
DAY = {"range": "day"}


# A fresh call log and the mock calendar tools that write to it.
def fresh():
    log = []
    return log, by_name(mock_calendar_tools(log))


# Run the agent on one user message with the fixed "now".
def run(text: str, chat, tools, max_steps: int = 6) -> dict:
    state = {"messages": [HumanMessage(text)], "plan": [text], "agent_results": {}}
    return run_agent(state, chat, tools, max_steps, NOW, CONFIG)


# The tool names the first step's schema offered the model.
def offered(chat) -> set[str]:
    schema = chat.calls[0]["output_model"].model_json_schema()
    return {ref["$ref"].split("_", 1)[1] for ref in schema["anyOf"]}


# The model gives only the title; the code-filled call has the parser's exact times.
def test_done_when_phrase_creates_the_right_event_with_code_filled_times():
    log, tools = fresh()
    chat = FakeChat({"create_event": {"title": "Meeting with Rahul"}},
                    {"done": {"summary": "Added."}})
    out = run(DONE_WHEN, chat, tools)
    full = {"title": "Meeting with Rahul", "start": TUE_10, "end": TUE_11}
    assert out["stopped"] == "done"
    assert [(c.tool, c.args) for c in log] == [("create_event", full)]
    assert out["steps"][0]["args"] == full  # the step records the filled call
    prompt = chat.calls[0]["messages"][0]["content"]
    assert "- Event time: Tue 17 Nov, 10:00-11:00 am" in prompt
    assert "Never write dates or times" in prompt


# No date fields anywhere in the schema the model fills in, for any calendar message.
def test_model_schema_has_no_date_fields():
    for text in (DONE_WHEN, "3 baje wali meeting 5 baje kar do", "Saturday subah clear kar do",
                 "Thursday dopahar free hoon?", "What is on my calendar?"):
        _, tools = fresh()
        chat = FakeChat(None)  # invalid reply: stops after step 1
        run(text, chat, tools)
        schema = json.dumps(chat.calls[0]["output_model"].model_json_schema())
        for word in ('"start"', '"end"', "date-time", '"date"'):
            assert word not in schema, (text, word)


# Range names: window and day from the words; today and next_7_days without a date.
def test_range_names_follow_the_words():
    for text, names in (("Thursday dopahar free hoon?", ["window", "day"]),
                        ("Saturday ko kya kya hai?", ["day"]),
                        ("What is on my calendar?", ["today", "next_7_days"])):
        _, tools = fresh()
        chat = FakeChat(None)
        run(text, chat, tools)
        field = chat.calls[0]["output_model"].model_json_schema()["$defs"]["RangeArgs"][
            "properties"]["range"]
        assert field.get("enum", [field.get("const")]) == names, text


def test_free_slots_by_range_name_gets_the_window():
    log, tools = fresh()
    chat = FakeChat({"find_free_slots": {"range": "window"}}, {"done": {"summary": "ok"}})
    run("Thursday dopahar free hoon?", chat, tools)
    assert log[0].args == {"start": "2026-11-19T12:00:00+05:30",
                           "end": "2026-11-19T16:00:00+05:30"}


def test_move_by_event_id_gets_the_new_time():
    log, tools = fresh()
    chat = FakeChat({"get_events": DAY}, {"move_event": {"event_id": "mock-evt-team"}},
                    {"done": {"summary": "Moved."}})
    run("3 baje wali meeting 5 baje kar do", chat, tools)
    assert [c.tool for c in log] == ["get_events", "move_event"]
    assert log[1].args == {"event_id": "mock-evt-team", "start": "2026-11-16T17:00:00+05:30",
                           "end": "2026-11-16T18:00:00+05:30"}


# M1.8 fix round: code fills the id of the listed event starting at the first
# time, so a wrong or garbled id from the model is replaced.
def test_move_id_comes_from_the_listed_event_at_the_first_time():
    for model_id in ("mock-evt-gym", "mock-evt-team”, "):
        log, tools = fresh()
        chat = FakeChat({"get_events": DAY}, {"move_event": {"event_id": model_id}})
        out = run("3 baje wali meeting 5 baje kar do", chat, tools)
        assert [c.tool for c in log] == ["get_events", "move_event"]
        assert out["steps"][1]["args"]["event_id"] == "mock-evt-team"


# Before get_events has listed anything, the model's id is kept and the guard refuses it.
def test_move_before_get_events_is_still_refused():
    log, tools = fresh()
    chat = FakeChat({"move_event": {"event_id": "123456"}}, None)
    out = run("3 baje wali meeting 5 baje kar do", chat, tools)
    assert log == [] and "call get_events first" in out["steps"][0]["result"]["error"]


def test_move_with_two_day_words_asks_without_llm():
    log, tools = fresh()
    chat = FakeChat(None)
    out = run("kal ki 3 baje wali meeting parso 5 baje kar do", chat, tools)
    assert out == {"steps": [], "summary": TWO_DAYS, "stopped": "ask"}
    assert chat.calls == [] and log == []


def test_two_times_with_a_create_word_asks():
    log, tools = fresh()
    chat = FakeChat(None)
    out = run("kal 3 baje se 5 baje tak workshop add karo", chat, tools)
    assert out == {"steps": [], "summary": ADD_OR_MOVE, "stopped": "ask"}
    assert chat.calls == [] and log == []


# A create with a date but no time: code asks "kis time?" instead of acting.
def test_create_with_date_but_no_time_asks_for_the_time():
    log, tools = fresh()
    out = run("Thursday ko Rahul se milna hai",
              FakeChat({"create_event": {"title": "Meet Rahul"}}), tools)
    assert (out["stopped"], out["summary"], log) == ("ask", ASK_TIME, [])
    assert f"- calendar: ask the user this question: {ASK_TIME}" in fact_lines(
        {"calendar": out})


# Two different refused cancels in one run both reach call_tool; the responder
# is told neither was done.
def test_two_different_refused_cancels_both_reach_call_tool():
    log, tools = fresh()
    chat = FakeChat({"get_events": {"range": "window"}},
                    {"cancel_event": {"event_id": "mock-evt-gym"}},
                    {"cancel_event": {"event_id": "mock-evt-call"}},
                    {"done": {"summary": "Asked."}})
    out = run("Saturday subah clear kar do", chat, tools)
    refused = [s["args"]["event_id"] for s in out["steps"][1:]
               if s["result"].get("needs_approval") is True]
    assert refused == ["mock-evt-gym", "mock-evt-call"] and out["stopped"] == "done"
    assert [c.tool for c in log] == ["get_events"]
    lines = fact_lines({"calendar": out})
    assert ("- calendar: cancel event 'Call', Sat 21 Nov, 10:00-10:30 am: NOT done, it "
            "needs the user's approval first") in lines


# Repeating the same refused cancel ends the run (it is not retried).
def test_same_refused_cancel_is_not_retried():
    _, tools = fresh()
    chat = FakeChat({"get_events": DAY}, {"cancel_event": {"event_id": "mock-evt-gym"}},
                    {"cancel_event": {"event_id": "mock-evt-gym"}})
    out = run("Saturday ka gym cancel kar do", chat, tools)
    assert out["stopped"] == "repeated_call" and len(out["steps"]) == 2


def test_add_message_never_offers_cancel_or_move():
    for text in (DONE_WHEN, "Add a dentist appointment on Thursday at 4:30 pm"):
        _, tools = fresh()
        chat = FakeChat(None)
        run(text, chat, tools)
        assert offered(chat) == {"get_events", "find_free_slots", "create_event"}
        assert "cancel_event(" not in chat.calls[0]["messages"][0]["content"]


def test_clear_message_offers_cancel_and_two_times_offer_move():
    _, tools = fresh()
    chat = FakeChat(None)
    run("Saturday subah clear kar do", chat, tools)
    assert "cancel_event" in offered(chat) and "move_event" not in offered(chat)
    chat = FakeChat(None)
    run("3 baje wali meeting 5 baje kar do", chat, tools)
    assert offered(chat) == {"get_events", "find_free_slots", "move_event"}


# Through the graph: the supervisor routes to calendar; the responder sees the
# event with its time in words.
def test_graph_routes_to_calendar_and_responder_sees_event_in_words():
    log, tools = fresh()
    chat = FakeChat({"agents": ["calendar"], "task": "Add meeting with Rahul"},
                    {"create_event": {"title": "Meeting with Rahul"}},
                    "Ho gaya! Kal 10 baje Rahul ke saath meeting daal di.")
    agents = {"calendar": calendar_agent(chat, tools, 6, CONFIG, now=lambda: NOW)}
    out = build_graph(chat, agents=agents).invoke(
        {"messages": [HumanMessage(DONE_WHEN)], "hops": 0, "plan": []})
    assert "- calendar: the user's own calendar" in chat.calls[0]["messages"][0]["content"]
    assert [c.tool for c in log] == ["create_event"]
    seen = " ".join(m["content"] for m in chat.calls[-1]["messages"])
    assert "Created 'Meeting with Rahul', Tue 17 Nov, 10:00-11:00 am" in seen
    assert out["messages"][-1].content.startswith("Ho gaya!")


# M1.8: a single create ends the run in code; the outcome says the am/pm was assumed.
def test_single_create_ends_without_done_call_and_reports_assumed_ampm():
    log, tools = fresh()
    chat = FakeChat({"create_event": {"title": "Dentist"}})
    out = run("Kal 4 baje dentist appointment daal do", chat, tools)
    assert len(chat.calls) == 1 and out["stopped"] == "done"
    assert log[0].args["start"] == "2026-11-17T16:00:00+05:30"
    assert out["assumed_ampm"] is True
    assert run(DONE_WHEN, FakeChat({"create_event": {"title": "x"}}), fresh()[1])[
        "assumed_ampm"] is False


# M1.8: with "aur" (two requests), a create does not end the run: the cancels still come.
def test_linked_requests_keep_asking_the_model():
    _, tools = fresh()
    chat = FakeChat({"create_event": {"title": "Lonavala trip"}},
                    {"get_events": {"range": "window"}},
                    {"cancel_event": {"event_id": "mock-evt-gym"}},
                    {"cancel_event": {"event_id": "mock-evt-call"}},
                    {"done": {"summary": "ok"}})
    out = run("Saturday subah 7 baje Lonavala trip plan kar do, aur Saturday subah clear kar do",
              chat, tools)
    assert [s["tool"] for s in out["steps"]] == ["create_event", "get_events",
                                                 "cancel_event", "cancel_event"]
    assert len(chat.calls) == 5


# M1.8: a read ends the run when nothing is to change; before a move it does not.
def test_read_ends_the_run_only_when_nothing_changes():
    chat = FakeChat({"get_events": DAY})
    assert run("Saturday ko kya kya hai?", chat, fresh()[1])["stopped"] == "done"
    assert len(chat.calls) == 1
    chat = FakeChat({"get_events": DAY}, {"move_event": {"event_id": "mock-evt-team"}})
    out = run("3 baje wali meeting 5 baje kar do", chat, fresh()[1])
    assert [s["tool"] for s in out["steps"]] == ["get_events", "move_event"]
    assert len(chat.calls) == 2


# M1.8: free time for a whole day uses waking hours; get_events keeps the whole day.
def test_free_slots_for_a_day_use_waking_hours_and_events_the_whole_day():
    log, tools = fresh()
    run("Saturday ko free time kab hai?", FakeChat({"find_free_slots": DAY}), tools)
    assert log[0].args == {"start": "2026-11-21T06:00:00+05:30",
                           "end": "2026-11-21T23:00:00+05:30"}
    log, tools = fresh()
    run("Saturday ko kya kya hai?", FakeChat({"get_events": DAY}), tools)
    assert log[0].args == {"start": "2026-11-21T00:00:00+05:30",
                           "end": "2026-11-22T00:00:00+05:30"}
