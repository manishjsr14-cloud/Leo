"""Tests for leo/memory/memory_history.py (M2.3 fix round): replaced memories are
kept as history, and a wrong replacement can be undone."""

import sqlite3
from datetime import datetime

import pytest

from leo.memory.memories import all_memories, save_memory, search_memories
from leo.memory.memory_history import history, undo_replacement
from tests.memory_fakes import make_bank

NOW = datetime(2026, 11, 26, 20, 0)
NAME = "Meri behen ka naam Priya hai."
BIRTHDAY = "Meri behen ka birthday 12 March ko hai."


# Active (subject, text) pairs, oldest first.
def active(bank) -> list[tuple[str, str]]:
    return [(r["subject"], r["text"]) for r in all_memories(bank)]


# The texts a search over all memories finds.
def found_texts(bank) -> set[str]:
    return {m.text for m in search_memories(bank, bank.embedder.embed_query("behen"), 5)}


# The M2.3 check's wrong replacement: the birthday stored under sister_name
# leaves the name in the history, and undo with the right subject keeps both.
def test_sister_case_name_is_recoverable(tmp_path):
    bank = make_bank(tmp_path)
    name_id, _ = save_memory(bank, "sister_name", NAME, "hinglish", NOW)
    birthday_id, replaced = save_memory(bank, "sister_name", BIRTHDAY, "hinglish", NOW)
    assert replaced and active(bank) == [("sister_name", BIRTHDAY)]
    assert [(r["text"], r["active"]) for r in history(bank, "sister_name")] == [
        (NAME, 0), (BIRTHDAY, 1)]
    restored = undo_replacement(bank, birthday_id, NOW, new_subject="sister_birthday")
    assert restored == name_id
    assert sorted(active(bank)) == [("sister_birthday", BIRTHDAY), ("sister_name", NAME)]
    assert found_texts(bank) == {NAME, BIRTHDAY}
    assert bank.conn.execute("SELECT count(*) FROM vec_memories").fetchone()[0] == 2


# Undo without a new subject: the old fact is back, the replacing one is inactive
# history (still not deleted).
def test_undo_without_new_subject(tmp_path):
    bank = make_bank(tmp_path)
    save_memory(bank, "sister_name", NAME, "hinglish", NOW)
    birthday_id, _ = save_memory(bank, "sister_name", BIRTHDAY, "hinglish", NOW)
    undo_replacement(bank, birthday_id, NOW)
    assert active(bank) == [("sister_name", NAME)]
    assert found_texts(bank) == {NAME}
    assert [r["text"] for r in history(bank, "sister_name")] == [NAME, BIRTHDAY]


# Undo refuses a memory that replaced nothing, and a bad new subject.
def test_undo_refuses_bad_requests(tmp_path):
    bank = make_bank(tmp_path)
    name_id, _ = save_memory(bank, "sister_name", NAME, "hinglish", NOW)
    with pytest.raises(ValueError):
        undo_replacement(bank, name_id, NOW)
    birthday_id, _ = save_memory(bank, "sister_name", BIRTHDAY, "hinglish", NOW)
    with pytest.raises(ValueError):
        undo_replacement(bank, birthday_id, NOW, new_subject="!!")
    assert active(bank) == [("sister_name", BIRTHDAY)]


# The database allows only one active memory per subject.
def test_one_active_memory_per_subject(tmp_path):
    bank = make_bank(tmp_path)
    save_memory(bank, "diet", "I eat non-veg food.", "en", NOW)
    with pytest.raises(sqlite3.IntegrityError):
        bank.conn.execute("INSERT INTO memories (subject, text, language, created_at, updated_at)"
                          " VALUES ('diet', 'x', 'en', 'a', 'a')")
