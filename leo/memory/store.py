"""Open Leo's SQLite database (architecture section 7).

M1.4 needs only a connection with the right settings and the tables from
schema.sql. M2.1 adds sqlite-vec and the VectorStore interface here.
Nothing happens at import time: the folder and file are created only when
open_db is called, so importing Leo or running tests never creates leo_data/.
"""

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


# Open (and create if needed) the database at `path`, with WAL mode,
# a 5 s busy timeout and all tables from schema.sql. Rows come back as
# sqlite3.Row so columns can be read by name. Only the server process
# writes, through this one connection (section 7), so it may be used
# from LangGraph's worker threads.
def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn
