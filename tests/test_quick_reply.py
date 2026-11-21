"""Tests for code-written replies to a single successful write (leo/graph/quick_reply.py)."""

from langchain_core.messages import HumanMessage

from leo.graph.quick_reply import quick_reply
from leo.graph.responder import responder_node
from tests.graph_fakes import FakeChat

EVENT = {"id": "e1", "title": "Call with Neha", "start": "2026-11-20T18:30:00+05:30",
         "end": "2026-11-20T19:30:00+05:30"}


# A state where one agent made one step with this tool and result.
def state(tool: str, result, language: str = "en", agent: str = "calendar", **outcome) -> dict:
    step = {"tool": tool, "args": {}, "result": result}
    return {"messages": [HumanMessage("x")], "language": language,
            "agent_results": {agent: {"steps": [step], "stopped": "done", **outcome}}}


def test_created_event_in_english_and_hinglish():
    assert quick_reply(state("create_event", EVENT)) == (
        "Done! Added 'Call with Neha' on Fri 20 Nov, 6:30-7:30 pm.")
    assert quick_reply(state("create_event", EVENT, "hinglish")) == (
        "Ho gaya! 'Call with Neha' Fri 20 Nov, 6:30-7:30 pm calendar mein daal diya.")


def test_assumed_am_pm_is_asked_as_a_question():
    en = quick_reply(state("create_event", EVENT, assumed_ampm=True))
    assert en.endswith("Did you mean 6:30 pm?")
    hinglish = quick_reply(state("create_event", EVENT, "hinglish", assumed_ampm=True))
    assert hinglish.endswith("6:30 pm hi chahiye tha na?")


def test_completed_task_never_says_already():
    done = {"id": 1, "title": "Buy milk", "done": True}
    assert quick_reply(state("complete_task", done, agent="productivity")) == (
        "Marked 'Buy milk' as done.")
    assert "already" not in quick_reply(state("complete_task", done, "hinglish"))


def test_timer_and_calculation():
    timer = {"label": "chai", "minutes": 10.0}
    assert quick_reply(state("start_timer", timer, "hinglish")) == (
        "'chai' ka timer 10 minute ke liye laga diya.")
    calc = {"expression": "12% of 900", "computed": "(12/100)*900", "result": "108"}
    assert quick_reply(state("calculate", calc)) == "12% of 900 = 108."


def test_reads_hindi_and_failures_go_to_the_llm():
    assert quick_reply(state("get_events", [EVENT])) is None
    assert quick_reply(state("create_event", EVENT, "hi")) is None
    assert quick_reply(state("create_event", {"error": "bad"})) is None
    assert quick_reply(state("create_event", EVENT, stopped="ask")) is None


def test_two_steps_or_two_agents_go_to_the_llm():
    two = state("create_event", EVENT)
    two["agent_results"]["calendar"]["steps"] *= 2
    assert quick_reply(two) is None
    both = state("create_event", EVENT)
    both["agent_results"]["research"] = {"steps": [], "stopped": "done"}
    assert quick_reply(both) is None


def test_responder_makes_no_llm_call_for_a_quick_reply():
    chat = FakeChat("should not be used")
    out = responder_node(state("create_event", EVENT), chat)
    assert chat.calls == []
    assert out["messages"][0].response_metadata["provider"] == "code"
