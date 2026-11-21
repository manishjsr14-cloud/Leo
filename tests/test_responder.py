"""Tests for the responder: only successful results reach the reply, as facts in
words (no raw JSON), in the language of the message (M1.8)."""

from langchain_core.messages import HumanMessage

from leo.graph.responder import (
    NO_ACTION_NOTE,
    PROMPT,
    responder_messages,
    responder_node,
)
from tests.graph_fakes import FakeChat

ASK = {"messages": [HumanMessage("what is 18% of 2450")]}
GYM = {"id": "g", "title": "Gym", "start": "2026-11-21T08:00:00+05:30",
       "end": "2026-11-21T09:00:00+05:30"}
CALL = {"id": "c", "title": "Call", "start": "2026-11-21T10:00:00+05:30",
        "end": "2026-11-21T10:30:00+05:30"}


# Everything the responder sent to the LLM after its fixed system prompt, as one string.
def sent(chat: FakeChat, call: int = 0) -> str:
    return " ".join(m["content"] for m in chat.calls[call]["messages"][1:])


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


# (b) A successful result reaches the responder in words, with no raw JSON.
def test_successful_calculate_is_sent_in_words_without_json():
    result = {"expression": "18% of 2450", "computed": "(18/100)*2450", "result": "441"}
    step = {"tool": "calculate", "args": {"expression": "18% of 2450"}, "result": result}
    chat = FakeChat("18% of 2450 is 441.")
    responder_node({**ASK, "agent_results": {"productivity": {"steps": [step, step]}}}, chat)
    text = sent(chat)
    assert "18% of 2450 = 441" in text
    assert "{" not in text and "In words" not in text


# Only failed steps are dropped: a good step after a failed one is kept.
def test_failed_steps_are_dropped_and_good_ones_kept():
    bad = {"tool": "complete_task", "args": {"task_id": 9}, "result": {"error": "no task"}}
    good = {"tool": "complete_task", "args": {"task_id": 1},
            "result": {"id": 1, "title": "milk", "done": True}}
    chat = FakeChat("Done.")
    responder_node({**ASK, "agent_results": {"productivity": {"steps": [bad, good]}}}, chat)
    text = sent(chat)
    assert "no task" not in text and "Marked task 'milk' as done" in text


# A plain chat turn (no agent ran) has no facts and no note.
def test_plain_chat_has_no_facts():
    chat = FakeChat("Hi!")
    responder_node({"messages": [HumanMessage("hi")]}, chat)
    assert "Facts" not in sent(chat)


# The reply language is the LAST line the model reads (M1.8 fix round).
def test_reply_language_follows_the_tag_and_comes_last():
    hinglish = responder_messages({"messages": [HumanMessage("x")], "language": "hinglish"})
    assert "Hinglish" in hinglish[-1]["content"] and "never Devanagari" in hinglish[-1]["content"]
    english = responder_messages({"messages": [HumanMessage("x")], "language": "en"})
    assert english[-1] == {"role": "system", "content": "Reply in English."}


# Today's date comes from the agent's own "today" (a check can fix it).
def test_today_comes_from_the_agent():
    state = {"messages": [HumanMessage("x")], "language": "en",
             "agent_results": {"calendar": {"steps": [], "today": "2026-11-16"}}}
    assert "Today is Monday 16 Nov 2026." in responder_messages(state)[0]["content"]


def test_devanagari_reply_to_roman_text_is_asked_again_once():
    chat = FakeChat("नहीं, बारिश नहीं होगी।", "Nahi, baarish nahi hogi.")
    out = responder_node({"messages": [HumanMessage("Kal baarish hogi?")],
                          "language": "hinglish"}, chat)
    assert len(chat.calls) == 2
    assert out["messages"][0].content == "Nahi, baarish nahi hogi."


def test_devanagari_reply_to_hindi_is_kept():
    chat = FakeChat("नहीं, बारिश नहीं होगी।")
    responder_node({"messages": [HumanMessage("कल बारिश होगी?")], "language": "hi"}, chat)
    assert len(chat.calls) == 1


def test_refused_cancel_is_named_and_the_rest_is_still_on_the_calendar():
    steps = [{"tool": "get_events", "args": {}, "result": [GYM, CALL]},
             {"tool": "cancel_event", "args": {"event_id": "g"},
              "result": {"error": "needs approval", "needs_approval": True}}]
    chat = FakeChat("Gym and Call are still on; nothing was cancelled.")
    state = {"messages": [HumanMessage("Saturday subah clear kar do")],
             "agent_results": {"calendar": {"steps": steps, "stopped": "done"}}}
    responder_node(state, chat)
    text = sent(chat)
    assert "cancel event 'Gym', Sat 21 Nov, 8:00-9:00 am: NOT done" in text
    assert "Still on the calendar: 'Gym', Sat 21 Nov, 8:00-9:00 am; 'Call'" in text


def test_responder_prompt_forbids_adding_facts():
    assert "never add facts, numbers, times or plans" in PROMPT.system
