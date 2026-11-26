"""Tests for leo/memory/memories.py (M2.3, M2.3b): saving, adding, replacing by id, searching."""

import sqlite3
from datetime import datetime

import pytest

from leo.memory.memories import (
    Memory,
    all_memories,
    clean_subject,
    save_memory,
    search_memories,
    top_hints,
)
from tests.memory_fakes import make_bank

NOW = datetime(2026, 11, 26, 10, 0)
EATS = "I eat non-veg food."
STOPPED = "I don't eat non-veg anymore."


# The vec_memories row count.
def vector_count(bank) -> int:
    return bank.conn.execute("SELECT count(*) FROM vec_memories").fetchone()[0]


# M2.3b: a fact on the same subject is ADDED unless the caller names what it
# replaces ("allergic to peanuts" and "allergic to dust" are both kept).
def test_same_subject_without_replaces_adds(tmp_path):
    bank = make_bank(tmp_path)
    first_id, replaced_first = save_memory(bank, "allergy", "Mujhe peanuts se allergy hai.",
                                           "hinglish", NOW)
    second_id, replaced_second = save_memory(bank, "allergy", "I'm also allergic to dust.",
                                             "en", NOW)
    assert (replaced_first, replaced_second) == ([], [])
    assert [r["id"] for r in all_memories(bank)] == [first_id, second_id]
    assert vector_count(bank) == 2


# The plan's M2.3 note, M2.3b form: a fact that names the memory it replaces
# makes it inactive history pointing at the new one; only its vector is removed,
# so a search finds only the new fact.
def test_replaces_makes_the_old_fact_history(tmp_path):
    bank = make_bank(tmp_path)
    first_id, _ = save_memory(bank, "diet", EATS, "en", NOW)
    second_id, replaced = save_memory(bank, "diet", STOPPED, "en", NOW, replaces=[first_id])
    assert replaced == [first_id]
    old = bank.conn.execute("SELECT * FROM memories WHERE id = ?", (first_id,)).fetchone()
    assert (old["text"], old["active"], old["replaced_by"]) == (EATS, 0, second_id)
    assert [(r["subject"], r["text"]) for r in all_memories(bank)] == [("diet", STOPPED)]
    assert vector_count(bank) == 1
    found = search_memories(bank, bank.embedder.embed_query("Do I eat meat?"), 5)
    assert [m.text for m in found] == [STOPPED]


# Replacing works across subjects, and an id that is not active is ignored.
def test_replaces_any_active_id_only(tmp_path):
    bank = make_bank(tmp_path)
    gym_id, _ = save_memory(bank, "gym", "Mera gym Aundh mein hai.", "hinglish", NOW)
    new_id, replaced = save_memory(bank, "workout", "Maine gym chhod diya.", "hinglish", NOW,
                                   replaces=[gym_id, 999])
    assert replaced == [gym_id]
    _, again = save_memory(bank, "workout", "Ab ghar pe.", "hinglish", NOW, replaces=[gym_id])
    assert again == []
    assert next(r["id"] for r in all_memories(bank)) == new_id


# Facts on different subjects are both kept.
def test_different_subjects_are_both_kept(tmp_path):
    bank = make_bank(tmp_path)
    save_memory(bank, "sister_birthday", "Meri behen ka birthday 12 March ko hai.", "hinglish", NOW)
    save_memory(bank, "brother_birthday", "My brother's birthday is on 5 June.", "en", NOW)
    assert [r["subject"] for r in all_memories(bank)] == ["sister_birthday", "brother_birthday"]
    assert vector_count(bank) == 2


# Stored facts are embedded as passages (the e5 "passage: " prefix), with the
# subject in words first (M2.3 fix round); the stored text is the user's words only.
def test_facts_are_embedded_with_their_subject(tmp_path):
    bank = make_bank(tmp_path)
    save_memory(bank, "brother_birthday", "My brother's birthday is on 5 June.", "en", NOW)
    assert bank.embedder.model.encoded == [
        "passage: brother birthday: My brother's birthday is on 5 June."]
    assert all_memories(bank)[0]["text"] == "My brother's birthday is on 5 June."


# Subject keys are short snake_case; anything else is refused.
@pytest.mark.parametrize("raw, key", [("diet", "diet"), ("Home City", "home_city"),
                                      ("sister-birthday", "sister_birthday"), ("x", None),
                                      ("1st_job", None), ("diet; drop table", None), ("", None)])
def test_clean_subject(raw, key):
    assert clean_subject(raw) == key


# A bad subject or empty text stores nothing.
def test_bad_subject_or_empty_text_is_refused(tmp_path):
    bank = make_bank(tmp_path)
    with pytest.raises(ValueError):
        save_memory(bank, "??", EATS, "en", NOW)
    with pytest.raises(ValueError):
        save_memory(bank, "diet", "  ", "en", NOW)
    assert all_memories(bank) == [] and vector_count(bank) == 0


# Only the user's own statements are memories: the table refuses any other source.
def test_table_accepts_only_user_source(tmp_path):
    bank = make_bank(tmp_path)
    with pytest.raises(sqlite3.IntegrityError):
        bank.conn.execute("INSERT INTO memories (subject, text, language, source, created_at,"
                          " updated_at) VALUES ('diet', 'x', 'en', 'web', 'a', 'a')")


# An empty memory table gives no results.
def test_search_on_empty_store(tmp_path):
    bank = make_bank(tmp_path)
    assert search_memories(bank, bank.embedder.embed_query("hi"), 5) == []


# Hints (M2.3b): the recall_k nearest, with no similarity threshold.
def test_top_hints_takes_the_nearest_without_threshold(tmp_path):
    cfg = make_bank(tmp_path, recall_k=3).cfg
    found = [Memory(i, f"s{i}", f"t{i}", sim) for i, sim in
             enumerate([0.95, 0.9, 0.85, 0.81, 0.2])]
    assert [m.id for m in top_hints(found, cfg)] == [0, 1, 2]
    assert [m.id for m in top_hints([Memory(9, "s", "t", 0.1)], cfg)] == [9]
    assert top_hints([], cfg) == []
