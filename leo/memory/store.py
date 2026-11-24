"""Open Leo's SQLite database and define the VectorStore interface (section 7).

open_db gives the one connection the server writes through: WAL mode, a 5 s
busy timeout, sqlite-vec loaded and all tables from schema.sql. Only the
server process writes, through this one connection; nothing here enforces
that, it is a rule (section 7).

VectorStore is the interface memory code uses for vector search, so the
SQLite version (leo/memory/sqlite_vec.py) could later be swapped for another
store (section 7, "Future") without changing its callers.

Nothing happens at import time: the folder and file are created only when
open_db is called, so importing Leo or running tests never creates leo_data/.
"""

import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

import sqlite_vec

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


# Open (and create if needed) the database at `path`, with WAL mode,
# a 5 s busy timeout, the sqlite-vec extension and all tables from
# schema.sql. Rows come back as sqlite3.Row so columns can be read by name.
# Only the server process writes, through this one connection (section 7),
# so it may be used from LangGraph's worker threads.
def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    _load_sqlite_vec(conn)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


# Load the sqlite-vec extension into `conn`. Extension loading is turned on
# only for this one load and turned off again straight after.
def _load_sqlite_vec(conn: sqlite3.Connection) -> None:
    conn.enable_load_extension(True)
    try:
        sqlite_vec.load(conn)
    finally:
        conn.enable_load_extension(False)


@runtime_checkable
class VectorStore(Protocol):
    """What memory code needs from a vector store: add vectors, find the nearest."""

    # Store one vector per id; ids are the row ids of the rows they belong to.
    def add(self, ids: Sequence[int], vectors: Sequence[Sequence[float]]) -> None: ...

    # Return up to k (id, distance) pairs, nearest first.
    def search(self, vector: Sequence[float], k: int) -> list[tuple[int, float]]: ...
