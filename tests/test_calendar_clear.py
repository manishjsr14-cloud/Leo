"""Tests for the code clear and the code condition check (M1 exit check, section 4.5).
Fake LLM and mock tools only: leo/agents/calendar_clear.py, calendar_condition.py,
leo/graph/held_reply.py."""

from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage

from leo.agents.calendar import run_agent
from leo.agents.calendar_guard import ASK_DAY
from leo.config import load_config
from leo.graph.responder import responder_node
from leo.language.calendar_words import asks_to_cancel, asks_to_clear
from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.registry import by_name
from tests.graph_fakes import FakeChat

NOW = datetime(2026, 11, 16, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata"))  # Monday
CONFIG = load_config().calendar
SECTION_4_5 = ("Agar Saturday ko baarish nahi hogi to subah 7 baje Lonavala trip plan kar do, "
               "aur Saturday subah clear kar do.")
SAT_7, SAT_8 = "2026-11-21T07:00:00+05:30", "2026-11-21T08:00:00+05:30"


# Research results as the research agent leaves them: one get_weather with Saturday's rain chance.
def weather(saturday_pct: int) -> dict:
    days = [{"date": "2026-11-21", "day": "Saturday", "rain_chance_pct": saturday_pct,
             "rain_mm": 0.0}]
    return {"research": {"steps": [{"tool": "get_weather", "args": {"place": "Lonavala"},
                                    "result": {"place": "Lonavala", "days": days,
                                               "source": "mock"}}],
                         "stopped": "done"}}


# Run the calendar agent on one message after the given earlier results.
def run(text: str, chat, results: dict | None = None) -> tuple[dict, list]:
    log = []
    state = {"messages": [HumanMessage(text)], "plan": [text],
             "agent_results": dict(results or {})}
    out = run_agent(state, chat, by_name(mock_calendar_tools(log)), 6, NOW, CONFIG)
    return out, log


# The reply for that run, with the earlier results and the calendar outcome.
def reply(text: str, out: dict, results: dict, language: str) -> str:
    state = {"messages": [HumanMessage(text)], "language": language,
             "agent_results": {**results, "calendar": out}}
    chat = FakeChat("LLM reply")
    message = responder_node(state, chat)["messages"][0]
    assert chat.calls == []  # written by code
    return message.content


# Section 4.5 on a dry Saturday: code lists the morning and proposes both cancels
# (refused together for approval), then the model adds the trip. One LLM call.
def test_section_4_5_clears_in_code_and_still_adds_the_trip():
    chat = FakeChat({"create_event": {"title": "Lonavala trip"}})
    out, log = run(SECTION_4_5, chat, weather(5))
    assert [s["tool"] for s in out["steps"]] == ["get_events", "cancel_event",
                                                 "cancel_event", "create_event"]
    assert out["steps"][0]["args"] == {"start": "2026-11-21T06:00:00+05:30",
                                       "end": "2026-11-21T12:00:00+05:30"}
    assert out["approval"] == {"tool": "cancel_event",
                               "event_ids": ["mock-evt-gym", "mock-evt-call"]}
    assert all(s["result"]["needs_approval"] for s in out["steps"][1:3])
    assert [c.tool for c in log] == ["get_events", "create_event"]  # nothing cancelled
    assert log[1].args == {"title": "Lonavala trip", "start": SAT_7, "end": SAT_8}
    assert len(chat.calls) == 1 and out["stopped"] == "done" and "held" not in out


# A clear alone needs no LLM call.
def test_clear_alone_makes_no_llm_call():
    chat = FakeChat(None)
    out, _ = run("Saturday subah clear kar do", chat)
    assert chat.calls == [] and out["stopped"] == "done"
    assert out["approval"]["event_ids"] == ["mock-evt-gym", "mock-evt-call"]


# An empty range: listed, nothing to cancel, nothing waits for approval.
def test_clear_of_an_empty_range_proposes_no_cancel():
    out, _ = run("Sunday subah clear kar do", FakeChat(None))
    assert [s["tool"] for s in out["steps"]] == ["get_events"] and "approval" not in out


# A clear with no day in the words asks which day, and runs nothing.
def test_clear_without_a_day_asks():
    out, log = run("calendar clear kar do", FakeChat(None))
    assert out == {**out, "steps": [], "stopped": "ask", "summary": ASK_DAY} and log == []


# Questions about a clear morning are free-time queries: no cancel_event is proposed.
def test_clear_questions_never_propose_a_cancel():
    for text in ("Saturday subah khaali hai?", "Is my Saturday morning clear?"):
        assert not asks_to_clear(text) and not asks_to_cancel(text)
        chat = FakeChat({"find_free_slots": {"range": "window"}})
        out, log = run(text, chat)
        assert "cancel_event(" not in chat.calls[0]["messages"][0]["content"], text
        assert "cancel_event" not in [s["tool"] for s in out["steps"]], text
        assert [c.tool for c in log] == ["find_free_slots"], text
    for text in ("Saturday subah clear kar do", "Clear my Saturday morning",
                 "Saturday subah khaali kar do", "Clear out my Saturday"):
        assert asks_to_clear(text), text


# Rainy forecast: no create_event, and a code-written reply naming the forecast.
def test_rainy_forecast_means_no_create_and_the_reply_names_it():
    results = weather(70)
    out, log = run(SECTION_4_5, FakeChat(None), results)
    assert "create_event" not in [s["tool"] for s in out["steps"]]
    assert [c.tool for c in log] == ["get_events"]
    assert out["held"]["why"] == "rain" and out["held"]["rain_pct"] == 70
    text = reply(SECTION_4_5, out, results, "hinglish")
    assert "70% baarish" in text and "Sat 21 Nov" in text and "nahi daala" in text
    assert "'Gym'" in text and "'Call'" in text
    english = reply(SECTION_4_5, out, results, "en")
    assert "70% chance of rain" in english and "did not add" in english


# At the limit (40 %) the trip is still added.
def test_rain_at_the_limit_still_adds():
    chat = FakeChat({"create_event": {"title": "Lonavala trip"}})
    out, log = run("Agar Saturday ko baarish nahi hogi to subah 7 baje trip plan kar do",
                   chat, weather(CONFIG.rain_skip_percent))
    assert [c.tool for c in log] == ["create_event"] and "held" not in out


# A condition other than rain: nothing is added, and the reply asks to confirm.
def test_other_condition_means_no_create_and_a_confirmation_question():
    text = "Agar Rahul free ho to Saturday subah 7 baje meeting daal do"
    chat = FakeChat(None)
    out, log = run(text, chat, weather(5))
    assert log == [] and chat.calls == [] and out["held"]["why"] == "condition"
    answer = reply(text, out, weather(5), "hinglish")
    assert answer.endswith("?") and "7:00 am" in answer and "kuch nahi daala" in answer
    english = reply("If Rahul is free, add a meeting on Saturday at 7 am", out, {}, "en")
    assert english.endswith("?") and "condition" in english


# A rain condition with no forecast for that day: not added, the user is asked.
def test_rain_condition_without_a_forecast_asks():
    out, log = run("Agar Saturday ko baarish nahi hogi to subah 7 baje trip plan kar do",
                   FakeChat(None))
    assert log == [] and out["held"]["why"] == "no_forecast"
    assert reply("x", out, {}, "en").endswith("?")
