"""VectorStore on sqlite-vec (section 7).

One vec0 virtual table per kind of vector (for example vec_memories in
M2.3), using cosine distance. The row id of each vector is the id of the
row it belongs to in the ordinary table. The connection must come from
leo.memory.store.open_db, which loads the sqlite-vec extension.

Note: `import sqlite_vec` below is the installed package, not this file;
Python 3 imports are absolute.
"""

import re
import sqlite3
from collections.abc import Sequence

import sqlite_vec

# Table names go into the SQL text, so only plain names like vec_memories pass.
_TABLE_NAME = re.compile(r"^vec_[a-z_]+$")


class SqliteVecStore:
    """A VectorStore backed by one sqlite-vec vec0 table of fixed dimension."""

    # Remember the connection, table name and dimension, and create the
    # vec0 table if it does not exist yet.
    def __init__(self, conn: sqlite3.Connection, table: str, dim: int) -> None:
        if not _TABLE_NAME.match(table):
            raise ValueError(f"bad vector table name: {table!r}")
        if dim < 1:
            raise ValueError(f"dimension must be at least 1, got {dim}")
        self.conn = conn
        self.table = table
        self.dim = dim
        conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS {table} "
            f"USING vec0(embedding float[{dim}] distance_metric=cosine)"
        )
        conn.commit()

    # Store one vector per id and commit. Every vector must have the
    # table's dimension; nothing is stored if one is wrong.
    def add(self, ids: Sequence[int], vectors: Sequence[Sequence[float]]) -> None:
        if len(ids) != len(vectors):
            raise ValueError(f"{len(ids)} ids but {len(vectors)} vectors")
        rows = [(int(i), self._pack(v)) for i, v in zip(ids, vectors)]
        with self.conn:
            self.conn.executemany(
                f"INSERT INTO {self.table} (rowid, embedding) VALUES (?, ?)", rows
            )

    # Return up to k (id, cosine distance) pairs, nearest first.
    def search(self, vector: Sequence[float], k: int) -> list[tuple[int, float]]:
        if k < 1:
            raise ValueError(f"k must be at least 1, got {k}")
        rows = self.conn.execute(
            f"SELECT rowid, distance FROM {self.table} "
            "WHERE embedding MATCH ? AND k = ? ORDER BY distance",
            (self._pack(vector), k),
        ).fetchall()
        return [(int(r[0]), float(r[1])) for r in rows]

    # Check a vector's length and pack it as float32 bytes for sqlite-vec.
    def _pack(self, vector: Sequence[float]) -> bytes:
        if len(vector) != self.dim:
            raise ValueError(f"vector has {len(vector)} values, table needs {self.dim}")
        return sqlite_vec.serialize_float32(list(vector))
