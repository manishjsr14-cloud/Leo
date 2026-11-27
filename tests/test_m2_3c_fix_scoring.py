"""Tests for evals/m2_3c_fix_scoring.py: the offer must show the parser's date."""

from datetime import datetime

from evals.m2_3c_fix_scoring import event_miss, fix_parts

NOW = datetime.fromisoformat("2026-11-18T10:00:00+05:30")  # a Wednesday
OFFER = {"lang": "en", "text": "Team dinner on Saturday at 8 pm", "expect": "offer"}
ASK = {"lang": "hinglish", "text": "Kal Priya ke saath meeting", "expect": "ask"}
KAL = "Kal matlab aane wala kal (tomorrow) ya beeta hua kal (yesterday)?"


# A record with this reply and tool log.
def rec(reply: str, log: list | None = None) -> dict:
    return {"reply": reply, "tool_log": log or []}


# The right date and offer words pass; a wrong date, no offer words or a tool call miss.
def test_offer_rule():
    good = "Sat 21 Nov, 8:00 pm: should I add this to your calendar?"
    assert event_miss(OFFER, rec(good), NOW) is None
    assert event_miss(OFFER, rec(good.replace("Sat 21", "Sun 22")), NOW).startswith("parser's")
    assert event_miss(OFFER, rec("Sat 21 Nov, 8:00 pm. Nice!"), NOW) == "no offer words"
    assert event_miss(OFFER, rec(good, [{"tool": "get_events"}]), NOW) == "1 tool calls"


# The ask must be the parser's question word for word.
def test_ask_rule():
    assert event_miss(ASK, rec(KAL), NOW) is None
    assert event_miss(ASK, rec("Kal kab?"), NOW) == "not the question"


# All three parts met, from the records alone.
def test_fix_parts_met():
    data = {"event_statements": [{"id": "E1", **ASK}],
            "first_person_statements": [{"id": "N1"}],
            "requests": [{"id": "A1", "expect_write": "start_timer"}]}
    records = {"E1": rec(KAL), "N1": rec("ok"),
               "A1": rec("set", [{"tool": "start_timer", "args": {}, "result": {}}])}
    assert all(ok for _, ok in fix_parts(data, records, NOW))
