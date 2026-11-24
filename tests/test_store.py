"""Tests for leo/memory/store.py, always on a temporary database."""

import sqlite3
import subprocess
import sys

import pytest

from leo.config import PROJECT_ROOT
from leo.memory.store import open_db


# open_db creates missing folders, turns on WAL and makes both tables.
def test_open_db_creates_tables_with_wal(tmp_path):
    path = tmp_path / "sub" / "leo.db"
    conn = open_db(path)
    assert path.exists()
    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
    tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master")}
    assert {"tasks", "notes"} <= tables


# open_db loads the sqlite-vec extension, and turns extension loading off again.
def test_open_db_loads_sqlite_vec(tmp_path):
    conn = open_db(tmp_path / "leo.db")
    assert conn.execute("SELECT vec_version()").fetchone()[0].startswith("v")
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("SELECT load_extension('nothing_here')")


# Opening the same file twice keeps the data (the schema uses IF NOT EXISTS).
def test_open_db_twice_keeps_rows(tmp_path):
    path = tmp_path / "leo.db"
    conn = open_db(path)
    conn.execute("INSERT INTO notes (text, created_at) VALUES ('hi', 'now')")
    conn.commit()
    conn.close()
    again = open_db(path)
    assert again.execute("SELECT count(*) FROM notes").fetchone()[0] == 1


# The table checks reject an empty task title.
def test_empty_title_is_rejected(tmp_path):
    conn = open_db(tmp_path / "leo.db")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO tasks (title, created_at) VALUES ('', 'now')")


# Importing every M1.4 module in a fresh Python creates no leo_data/ folder.
# Skipped when leo_data/ already exists (for example after using the CLI).
def test_imports_do_not_create_leo_data():
    leo_data = PROJECT_ROOT / "leo_data"
    if leo_data.exists():
        pytest.skip("leo_data/ already exists on this machine")
    code = ("import leo.cli, leo.memory.store, leo.agents.productivity, "
            "leo.tools.registry, leo.tools.real.productivity")
    subprocess.run([sys.executable, "-c", code], cwd=PROJECT_ROOT, check=True)
    assert not leo_data.exists()
