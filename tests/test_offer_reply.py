"""Tests for the code-written offer after an event statement (M2.3c fix round a).

The examples are the test author's own, not the fix-round set's lines.
"""

from datetime import datetime

from langchain_core.messages import HumanMessage

from leo.graph.builder import build_graph
from leo.graph.offer_reply import offer_reply
from leo.graph.responder import responder_node
from leo.language.event_offer import event_time
from tests.graph_fakes import FakeChat

NOW = datetime.fromisoformat("2026-11-18T10:00:00+05:30")  # a Wednesday
KAL = "Kal matlab aane wala kal (tomorrow) ya beeta hua kal (yesterday)?"


# The state the responder sees after a statement in `language`.
def said(text: str, language: str = "en", kind: str = "statement") -> dict:
    return {"messages": [HumanMessage(text)], "turn_kind": kind, "language": language}


# An event word and a time the parser reads give the parser's date.
def test_event_time_reads_coming_events():
    assert str(event_time("Team dinner on Saturday", NOW).date) == "2026-11-21"
    assert event_time("Kal Priya ke saath meeting", NOW).status == "ask"


# No event word, a past-tense word, an unreadable time or a past date: no offer.
def test_event_time_none():
    assert event_time("Saturday is a holiday", NOW) is None                # no event word
    assert event_time("Kal mera interview hua", NOW) is None               # past word
    assert event_time("I had a call on Monday", NOW) is None               # past word
    assert event_time("Dinner with Ravi this evening", NOW) is None        # parser can't read
    assert event_time("Meeting at 9 am", NOW.replace(hour=23)) is not None  # next day, ok


# The offer shows the date and time, or part of the day, in the user's language.
def test_offer_text():
    assert offer_reply(said("Team dinner on Saturday at 8 pm"), NOW) == (
        "Sat 21 Nov, 8:00 pm: should I add this to your calendar?")
    assert offer_reply(said("Shukravaar ko lunch hai", "hinglish"), NOW) == (
        "Fri 20 Nov — kya main ise calendar mein daal doon?")
    assert offer_reply(said("Friday shaam ko party hai", "hinglish"), NOW) == (
        "Fri 20 Nov, shaam — kya main ise calendar mein daal doon?")


# The parser's question when it asks; nothing for a question or a request turn.
def test_ask_and_other_kinds():
    assert offer_reply(said("Kal Priya ke saath meeting", "hinglish"), NOW) == KAL
    assert offer_reply(said("Team dinner on Saturday?", kind="question"), NOW) is None
    assert offer_reply(said("Add team dinner on Saturday", kind="request"), NOW) is None


# The responder sends the offer without an LLM call, using the graph's now.
def test_responder_and_graph_use_the_offer():
    chat = FakeChat()
    out = responder_node(said("Team dinner on Saturday"), chat, now=NOW)
    assert out["messages"][0].content == "Sat 21 Nov: should I add this to your calendar?"
    assert chat.calls == []
    graph = build_graph(FakeChat(), agents={"x": lambda s: {}}, now=lambda: NOW)
    reply = graph.invoke({"messages": [HumanMessage("Team dinner on Saturday")],
                          "language": "en", "hops": 0, "plan": []})["messages"][-1]
    assert reply.content.startswith("Sat 21 Nov:")
