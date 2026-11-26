"""Tests for leo/graph/memory_nodes.py (M2.3, M2.3b) with a fake embedding model and fake LLM."""

from datetime import datetime

import pytest
from langchain_core.messages import HumanMessage

from leo.graph.memory_nodes import memory_recall_node, memory_write_node
from leo.llm.gateway import LLMUnavailable
from leo.memory.memories import all_memories, save_memory
from tests.graph_fakes import FakeChat
from tests.memory_fakes import make_bank

NOW = datetime(2026, 11, 26, 10, 0)
# Plans and events (none from the check set): code keeps them out, with no LLM call.
PLANS = ["I'm flying to Delhi next Monday.", "Meri parso doctor ke saath meeting hai.",
         "Main kal Nashik ja raha hoon.", "Mera aaj ka dinner bahar hai.",
         "I have a call with Ravi at 3 pm.", "My exam is on 14 April.",
         "Agle hafte mera interview hai."]


# A state for one turn: earlier messages (optional), then the user's message.
def turn(text: str, language: str = "en", **extra) -> dict:
    return {"messages": [*extra.pop("before", []), HumanMessage(text)], "language": language,
            **extra}


# A fake extraction reply.
def decision(subject: str, replaces: int = 0) -> dict:
    return {"subject": subject, "replaces": replaces}


# Write one message with a fixed time.
def write(text: str, bank, chat) -> dict:
    return memory_write_node(turn(text), bank, chat, now=lambda: NOW)


# Recall gives a personal question the recall_k nearest memories, with no
# threshold, and marks the turn as a personal question.
def test_recall_gives_nearest_hints_to_a_personal_question(tmp_path):
    table = {"Do I eat meat?": [1, 0, 0, 0], "diet: I don't eat non-veg anymore.": [1, 0.1, 0, 0],
             "car: My car is red.": [0, 1, 0, 0]}
    bank = make_bank(tmp_path, table, recall_k=1)
    save_memory(bank, "diet", "I don't eat non-veg anymore.", "en", NOW)
    save_memory(bank, "car", "My car is red.", "en", NOW)
    out = memory_recall_node(turn("Do I eat meat?"), bank)
    assert out == {"memories": ["I don't eat non-veg anymore."], "personal_question": True}
    far = memory_recall_node(turn("Mera passport number kya hai?"), bank)
    assert len(far["memories"]) == 1 and far["personal_question"]


# Other turns get no hints and are not embedded by recall.
@pytest.mark.parametrize("text", ["Will it rain tomorrow?", "I live in Nashik.",
                                  "add milk to the list", ""])
def test_recall_gate_stays_closed(tmp_path, text):
    bank = make_bank(tmp_path)
    save_memory(bank, "car", "My car is red.", "en", NOW)
    assert memory_recall_node(turn(text), bank) == {"memories": [], "personal_question": False}
    assert not [t for t in bank.embedder.model.encoded if t.startswith("query: ")]


# The message is embedded once in a turn, even when recall and write both run.
def test_message_is_embedded_once_per_turn(tmp_path):
    bank = make_bank(tmp_path)
    state = turn("I live in Nashik.")
    memory_recall_node(state, bank)
    memory_write_node(state, bank, FakeChat(decision("home_city")), now=lambda: NOW)
    queries = [t for t in bank.embedder.model.encoded if t.startswith("query: ")]
    assert queries == ["query: I live in Nashik."]


# A message the word rule does not pick makes no LLM call and stores nothing.
@pytest.mark.parametrize("text", ["add milk to my tasks", "Do I eat meat?", "Thanks!"])
def test_no_trigger_no_llm_call(tmp_path, text):
    bank, chat = make_bank(tmp_path), FakeChat(decision("x_y"))
    assert memory_write_node(turn(text), bank, chat) == {}
    assert chat.calls == [] and all_memories(bank) == []


# A picked message: one extraction call on the fact as delimited data; the fact
# is stored in the user's words, without "yaad rakhna", with the turn's language.
def test_trigger_stores_the_fact(tmp_path):
    bank, chat = make_bank(tmp_path), FakeChat(decision("blood_group"))
    memory_write_node(turn("Yaad rakhna, mera blood group O positive hai.", "hinglish"),
                      bank, chat, now=lambda: NOW)
    assert len(chat.calls) == 1
    assert chat.calls[0]["messages"][-1]["content"] == (
        "<message>\nmera blood group O positive hai.\n</message>")
    rows = all_memories(bank)
    assert [(r["subject"], r["text"], r["language"], r["source"]) for r in rows] == [
        ("blood_group", "mera blood group O positive hai.", "hinglish", "user")]


# No update cue: a fact on a stored subject is added, even if the model names a
# memory to replace; the call was shown the stored subject but no list.
def test_no_cue_adds_next_to_the_old_fact(tmp_path):
    bank = make_bank(tmp_path)
    chat = FakeChat(decision("allergy"), decision("allergy", 1))
    write("Mujhe peanuts se allergy hai.", bank, chat)
    write("I'm also allergic to dust.", bank, chat)
    system = chat.calls[1]["messages"][0]["content"]
    assert "Subjects already stored nearby: allergy" in system and "none (no update cue)" in system
    assert [r["text"] for r in all_memories(bank)] == [
        "Mujhe peanuts se allergy hai.", "I'm also allergic to dust."]


# The plan's M2.3 note, M2.3b form: with an update cue the call sees the nearby
# memories numbered, and the one it picks becomes history.
def test_cue_replaces_the_picked_memory(tmp_path):
    table = {"I don't eat non-veg anymore.": [1, 0, 0, 0],
             "diet: I eat non-veg food.": [1, 0.2, 0, 0], "car: My car is red.": [0, 1, 0, 0]}
    bank = make_bank(tmp_path, table)
    chat = FakeChat(decision("diet"), decision("car"), decision("diet", 1))
    write("I eat non-veg food.", bank, chat)
    write("My car is red.", bank, chat)
    write("I don't eat non-veg anymore.", bank, chat)
    assert "1. I eat non-veg food." in chat.calls[2]["messages"][0]["content"]
    assert [r["text"] for r in all_memories(bank)] == [
        "My car is red.", "I don't eat non-veg anymore."]
    old = bank.conn.execute("SELECT active, replaced_by FROM memories WHERE id = 1").fetchone()
    assert (old["active"], old["replaced_by"]) == (0, 3)


# With a cue, "replaces" 0 or a number not listed replaces nothing.
@pytest.mark.parametrize("pick", [0, 7, -1])
def test_cue_without_a_valid_pick_adds(tmp_path, pick):
    bank = make_bank(tmp_path)
    chat = FakeChat(decision("gym"), decision("gym", pick))
    write("Mera gym Aundh mein hai.", bank, chat)
    write("Maine gym chhod diya.", bank, chat)
    assert len(all_memories(bank)) == 2


# Plans and events are kept out by code: no LLM call, nothing stored.
@pytest.mark.parametrize("text", PLANS)
def test_plans_and_events_are_not_stored(tmp_path, text):
    bank, chat = make_bank(tmp_path), FakeChat(decision("plan"))
    write(text, bank, chat)
    assert chat.calls == [] and all_memories(bank) == []


# Known limit (M2.3b): a passing state with no time word is stored like a fact.
def test_passing_state_without_time_word_is_stored(tmp_path):
    bank = make_bank(tmp_path)
    write("I am really sleepy right now.", bank, FakeChat(decision("sleep")))
    assert len(all_memories(bank)) == 1


# A bad subject, an invalid reply, or no model: the fact is still stored, under "general".
@pytest.mark.parametrize("reply", [decision("!!"), decision(""), None])
def test_bad_extraction_stores_under_general(tmp_path, reply):
    bank = make_bank(tmp_path)
    write("I live in Nashik.", bank, FakeChat(reply))
    assert [(r["subject"], r["text"]) for r in all_memories(bank)] == [
        ("general", "I live in Nashik.")]


# A failed LLM after the reply must not break the turn; the fact is kept.
def test_llm_unavailable_stores_under_general(tmp_path):
    bank = make_bank(tmp_path)

    # A chat that always fails.
    def failing(messages, output_model=None, force_cloud=False):
        raise LLMUnavailable("down")

    assert write("I live in Nashik.", bank, failing) == {}
    assert [r["subject"] for r in all_memories(bank)] == ["general"]
