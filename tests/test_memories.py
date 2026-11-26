"""Tests for leo/memory/memories.py (M2.3): saving, replacing on the same subject, searching."""

import sqlite3
from datetime import datetime

import pytest

from leo.memory.memories import (
    Memory,
    all_memories,
    clean_subject,
    pick_hints,
    save_memory,
    search_memories,
)
from tests.memory_fakes import make_bank

NOW = datetime(2026, 11, 26, 10, 0)
EATS = "I eat non-veg food."
STOPPED = "I don't eat non-veg anymore."


# The vec_memories row count.
def vector_count(bank) -> int:
    return bank.conn.execute("SELECT count(*) FROM vec_memories").fetchone()[0]


# The plan's M2.3 note: a contradicting fact on the same subject replaces the old
# one (row and vector), so a search finds only the new fact.
def test_new_fact_on_same_subject_replaces_the_old_one(tmp_path):
    bank = make_bank(tmp_path)
    first_id, replaced_first = save_memory(bank, "diet", EATS, "en", NOW)
    second_id, replaced_second = save_memory(bank, "diet", STOPPED, "en", NOW)
    assert (replaced_first, replaced_second) == (False, True)
    assert second_id == first_id
    rows = all_memories(bank)
    assert [(r["subject"], r["text"]) for r in rows] == [("diet", STOPPED)]
    assert vector_count(bank) == 1
    query = bank.embedder.embed_query("Do I eat meat?")
    found = search_memories(bank, query, 5)
    assert [m.text for m in found] == [STOPPED]


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


# Hints: only at or above min_similarity, and at most recall_k of them, nearest first.
def test_pick_hints_threshold_and_count(tmp_path):
    cfg = make_bank(tmp_path, min_similarity=0.8, recall_k=3).cfg
    found = [Memory(i, f"s{i}", f"t{i}", sim) for i, sim in
             enumerate([0.95, 0.9, 0.85, 0.81, 0.79])]
    assert [m.id for m in pick_hints(found, cfg)] == [0, 1, 2]
    assert pick_hints([Memory(9, "s", "t", 0.79)], cfg) == []
    assert [m.id for m in pick_hints([Memory(9, "s", "t", 0.8)], cfg)] == [9]
