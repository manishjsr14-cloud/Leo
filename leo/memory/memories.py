"""Long-term memory: lasting facts and preferences (M2.3, architecture section 7).

Each memory is one row in `memories` (a subject key, the user's own words, the
language) plus one vector in `vec_memories` with the same id. There is at most
one memory per subject: saving a fact on a subject that already has one
REPLACES it (text and vector), so "I eat non-veg" followed by "I don't eat
non-veg anymore" leaves only the second. The embedder cannot tell those two
apart (0.984 in M2.2), so the subject key, not similarity, decides a replacement.

Stored texts are embedded as passages; messages are searched as queries
(the e5 prefixes, section 8.1). Similarity is 1 - cosine distance.
"""

import re
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from leo.config import MemoryConfig
from leo.memory.sqlite_vec import SqliteVecStore
from leo.memory.store import VectorStore

TABLE = "vec_memories"
SUBJECT = re.compile(r"^[a-z][a-z0-9_]{1,40}$")


@dataclass
class MemoryBank:
    """Everything memory code needs: the database, its vectors, the embedder, settings."""

    conn: sqlite3.Connection
    vectors: VectorStore
    embedder: object  # leo.ml.embedder.Embedder, or a fake in tests
    cfg: MemoryConfig


@dataclass(frozen=True)
class Memory:
    """One memory found by a search, with its cosine similarity to the message."""

    id: int
    subject: str
    text: str
    similarity: float


# Open the memory bank on a connection from open_db (creates vec_memories if needed).
def open_bank(conn: sqlite3.Connection, embedder, cfg: MemoryConfig, dim: int) -> MemoryBank:
    return MemoryBank(conn, SqliteVecStore(conn, TABLE, dim), embedder, cfg)


# A subject key in plain form: lower case, spaces and dashes as "_".
# Returns None when it is not a short snake_case key.
def clean_subject(subject: str) -> str | None:
    key = re.sub(r"[\s\-]+", "_", subject.strip().lower())
    return key if SUBJECT.match(key) else None


# Save one fact under its subject. Returns (memory id, True if an older fact on
# the same subject was replaced). The text is embedded before anything is written.
def save_memory(bank: MemoryBank, subject: str, text: str, language: str,
                now: datetime) -> tuple[int, bool]:
    key = clean_subject(subject)
    if key is None or not text.strip():
        raise ValueError(f"bad memory: subject={subject!r}")
    vector = bank.embedder.embed_passages([text.strip()])[0]
    stamp = now.isoformat(timespec="seconds")
    old = bank.conn.execute("SELECT id FROM memories WHERE subject = ?", (key,)).fetchone()
    with bank.conn:
        if old is None:
            cur = bank.conn.execute(
                "INSERT INTO memories (subject, text, language, source, created_at, updated_at)"
                " VALUES (?, ?, ?, 'user', ?, ?)", (key, text.strip(), language, stamp, stamp))
            memory_id = int(cur.lastrowid)
        else:
            memory_id = int(old["id"])
            bank.conn.execute(
                "UPDATE memories SET text = ?, language = ?, updated_at = ? WHERE id = ?",
                (text.strip(), language, stamp, memory_id))
    if old is not None:
        bank.vectors.delete([memory_id])
    bank.vectors.add([memory_id], [vector])
    return memory_id, old is not None


# The k memories nearest to a message vector, nearest first, with similarity.
def search_memories(bank: MemoryBank, vector: Sequence[float], k: int) -> list[Memory]:
    if bank.conn.execute("SELECT 1 FROM memories LIMIT 1").fetchone() is None:
        return []
    found = []
    for memory_id, distance in bank.vectors.search(vector, k):
        row = bank.conn.execute(
            "SELECT subject, text FROM memories WHERE id = ?", (memory_id,)).fetchone()
        if row is not None:
            found.append(Memory(memory_id, row["subject"], row["text"], 1.0 - distance))
    return found


# The hints for the reply: at most recall_k of the found memories, each at or
# above min_similarity.
def pick_hints(found: list[Memory], cfg: MemoryConfig) -> list[Memory]:
    return [m for m in found if m.similarity >= cfg.min_similarity][: cfg.recall_k]


# All memories, oldest first (for checks and, later, "what do you know about me?").
def all_memories(bank: MemoryBank) -> list[sqlite3.Row]:
    return bank.conn.execute("SELECT * FROM memories ORDER BY id").fetchall()
