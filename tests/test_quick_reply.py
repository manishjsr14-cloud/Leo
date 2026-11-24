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
    assert quick_reply(state("list_tasks", [{"id": 1}], agent="productivity")) is None
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


# M1 exit check (K06): a single find_free_slots gets a code reply naming every slot.
THU_FREE = [{"start": "2026-11-19T12:00:00+05:30", "end": "2026-11-19T13:00:00+05:30"},
            {"start": "2026-11-19T14:00:00+05:30", "end": "2026-11-19T16:00:00+05:30"}]


def test_free_slots_reply_lists_every_slot():
    assert quick_reply(state("find_free_slots", THU_FREE, "hinglish")) == (
        "Thu 19 Nov ko aap free ho: 12:00-1:00 pm aur 2:00-4:00 pm.")
    assert quick_reply(state("find_free_slots", THU_FREE)) == (
        "You're free on Thu 19 Nov: 12:00-1:00 pm and 2:00-4:00 pm.")
    three = [*THU_FREE, {"start": "2026-11-19T17:00:00+05:30", "end": "2026-11-19T18:00:00+05:30"}]
    assert quick_reply(state("find_free_slots", three)).endswith(
        "12:00-1:00 pm, 2:00-4:00 pm and 5:00-6:00 pm.")


def test_free_slots_on_several_days_and_none():
    days = [THU_FREE[0], {"start": "2026-11-20T09:00:00+05:30", "end": "2026-11-20T10:00:00+05:30"}]
    assert quick_reply(state("find_free_slots", days)) == (
        "You're free at these times: Thu 19 Nov, 12:00-1:00 pm and Fri 20 Nov, 9:00-10:00 am.")
    empty = state("find_free_slots", [], "hinglish")
    empty["agent_results"]["calendar"]["steps"][0]["args"] = {
        "start": "2026-11-19T12:00:00+05:30", "end": "2026-11-19T16:00:00+05:30"}
    assert quick_reply(empty) == "Thu 19 Nov, 12:00-4:00 pm mein aapka koi free time nahi hai."
    assert quick_reply(state("find_free_slots", THU_FREE, "hi")) is None


# The K06 reply passes the M1.8 reply rules the eval scores (both times, Hinglish).
def test_free_slots_reply_passes_the_eval_reply_rules():
    from evals.m1_8_scoring import language_ok, reply_fails

    text = quick_reply(state("find_free_slots", THU_FREE, "hinglish"))
    steps = [{"tool": "find_free_slots", "args": {"start": "2026-11-19T12:00:00+05:30",
                                                  "end": "2026-11-19T16:00:00+05:30"},
              "result": THU_FREE}]
    turn = {"text": "Thursday dopahar free hoon?", "reply_times_required": ["13:00", "14:00"]}
    assert reply_fails(text, turn, steps) == []
    assert language_ok(text, "hinglish")[0]


# M1 cleanup item 4: a single successful get_events gets a code reply naming
# every event with its time, in start order.
SAT_EVENTS = [
    {"id": "c", "title": "Call", "start": "2026-11-21T10:00:00+05:30",
     "end": "2026-11-21T10:30:00+05:30"},
    {"id": "g", "title": "Gym", "start": "2026-11-21T08:00:00+05:30",
     "end": "2026-11-21T09:00:00+05:30"}]
SAT_RANGE = {"start": "2026-11-21T06:00:00+05:30", "end": "2026-11-21T12:00:00+05:30"}


def test_events_reply_lists_every_event_on_one_day():
    assert quick_reply(state("get_events", SAT_EVENTS)) == (
        "On Sat 21 Nov you have: 'Gym' (8:00-9:00 am) and 'Call' (10:00-10:30 am).")
    assert quick_reply(state("get_events", SAT_EVENTS, "hinglish")) == (
        "Sat 21 Nov ko aapke calendar mein hai: 'Gym' (8:00-9:00 am) aur 'Call' (10:00-10:30 am).")


def test_events_reply_on_several_days_carries_each_day():
    assert quick_reply(state("get_events", [EVENT, SAT_EVENTS[1]])) == (
        "On your calendar: 'Call with Neha' (Fri 20 Nov, 6:30-7:30 pm) and "
        "'Gym' (Sat 21 Nov, 8:00-9:00 am).")


def test_events_reply_nothing_on():
    empty = state("get_events", [], "hinglish")
    empty["agent_results"]["calendar"]["steps"][0]["args"] = SAT_RANGE
    assert quick_reply(empty) == (
        "Sat 21 Nov, 6:00 am-12:00 pm mein aapke calendar mein kuch nahi hai.")
    empty["language"] = "en"
    assert quick_reply(empty) == "Nothing on your calendar in Sat 21 Nov, 6:00 am-12:00 pm."


def test_failed_or_followed_get_events_goes_to_the_llm():
    assert quick_reply(state("get_events", {"error": "bad range"})) is None
    moved = state("get_events", SAT_EVENTS)
    moved["agent_results"]["calendar"]["steps"].append(
        {"tool": "move_event", "args": {}, "result": SAT_EVENTS[1]})
    assert quick_reply(moved) is None
    assert quick_reply(state("get_events", SAT_EVENTS, "hi")) is None


# The events reply passes the M1.8 reply rules the eval scores, with v1 and v2.
def test_events_reply_passes_the_eval_reply_rules():
    from evals.language_scoring_v2 import language_ok_v2
    from evals.m1_8_scoring import language_ok, reply_fails

    text = quick_reply(state("get_events", SAT_EVENTS, "hinglish"))
    steps = [{"tool": "get_events", "args": SAT_RANGE, "result": SAT_EVENTS}]
    turn = {"text": "Saturday subah kya hai?", "reply_must_mention": ["Gym", "Call"]}
    assert reply_fails(text, turn, steps) == []
    assert language_ok(text, "hinglish", "Gym Call")[0]
    assert language_ok_v2(text, "hinglish", "Gym Call")[0]


# M1 cleanup item 4 follow-up: a message asking for a change that ended with only
# get_events gets a line saying the change was not made, in both languages.
def asked(text: str, language: str = "en") -> dict:
    s = state("get_events", SAT_EVENTS, language)
    s["messages"] = [HumanMessage(text)]
    return s


def test_events_reply_says_a_requested_change_was_not_made():
    en = quick_reply(asked("Cancel my Saturday gym"))
    assert en.startswith("On Sat 21 Nov you have: 'Gym' (8:00-9:00 am)")
    assert en.endswith("The change you asked for was not made; your calendar is as it was.")
    hinglish = quick_reply(asked("Saturday subah clear kar do", "hinglish"))
    assert hinglish.endswith("Aapne jo change bola tha woh nahi hua; calendar pehle jaisa hi hai.")
    for text in ("Move the call to 11 am", "Saturday ko gym daal do"):
        assert "not made" in quick_reply(asked(text))


def test_events_reply_for_a_question_has_no_change_line():
    for text in ("Saturday ko kya kya hai?", "What's on my calendar on Saturday?"):
        assert "not made" not in quick_reply(asked(text))
        assert "nahi hua" not in quick_reply(asked(text, "hinglish"))


# The change line passes the eval's reply rules, incl. "no invented results".
def test_change_line_passes_the_eval_reply_rules():
    from evals.eval_scoring import invented_results
    from evals.language_scoring_v2 import language_ok_v2
    from evals.m1_8_scoring import language_ok, reply_fails

    steps = [{"tool": "get_events", "args": SAT_RANGE, "result": SAT_EVENTS}]
    for text, lang in (("Cancel my Saturday gym", "en"), ("Saturday gym hata do", "hinglish")):
        reply = quick_reply(asked(text, lang))
        assert reply_fails(reply, {"text": text}, steps) == []
        assert invented_results(reply, steps) == []
        assert language_ok(reply, lang, "Gym Call")[0]
        assert language_ok_v2(reply, lang, "Gym Call")[0]
