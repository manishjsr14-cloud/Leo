"""Long-term memory for an eval suite run (M2.3b regression: the M1.10 suite with
memory on). The run works on a COPY of the given database, so the database a
check left behind is never changed; "empty" gives a new empty one. Copies live
in leo_data/evals/ (git-ignored) and are never overwritten.
"""

import sqlite3
import sys
from pathlib import Path

from leo.memory.memories import open_bank
from leo.memory.store import open_db
from leo.ml.embedder import load_embedder

DB_DIR = Path("leo_data/evals")


# A memory bank on a copy of `source` ("empty": a new database) named after the report.
def memory_copy(source: str, stem: Path, config):
    target = DB_DIR / f"{stem.name}_memory.db"
    if target.exists():
        sys.exit(f"{target} already exists; never overwritten.")
    DB_DIR.mkdir(parents=True, exist_ok=True)
    if source != "empty":
        if not Path(source).exists():
            sys.exit(f"{source} not found.")
        src, dst = sqlite3.connect(source), sqlite3.connect(target)
        src.backup(dst)
        src.close()
        dst.close()
    return open_bank(open_db(target), load_embedder(config.embedder), config.memory,
                     config.embedder.dimension)


# The number of memory rows (active or not), or None without memory.
def memory_count(bank) -> int | None:
    if bank is None:
        return None
    return bank.conn.execute("SELECT count(*) FROM memories").fetchone()[0]
