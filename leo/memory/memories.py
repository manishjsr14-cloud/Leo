"""Long-term memory: lasting facts and preferences (M2.3, architecture section 7).

Each memory is one row in `memories` (a subject key, the user's own words, the
language) plus one vector in `vec_memories` with the same id.
M2.3b: several active memories may share a subject ("allergic to peanuts" and
"allergic to dust"). A memory is replaced only when the message had an update
cue and named the memory it replaces (leo/graph/memory_nodes.py); the embedder
cannot tell a fact from its negation (0.984 in M2.2), so similarity alone never
replaces anything. A replaced memory is never deleted: it stays as inactive
history (its vector is removed, so it is never recalled) and a wrong
replacement can be undone (leo/memory/memory_history.py).

Stored texts are embedded as passages; messages are searched as queries
(the e5 prefixes, section 8.1). Similarity is 1 - cosine distance.
M2.3 fix round: the passage embedded is "<subject in words>: <fact>", e.g.
"brother birthday: My brother's birthday is on 5 June.", so a question in
Hinglish or with another word also meets the subject's English words. The
stored text stays the user's own words.
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


# The text that is embedded for a memory: its subject in words, then the fact.
def passage_text(subject: str, text: str) -> str:
    return f"{subject.replace('_', ' ')}: {text.strip()}"


# Embed a memory's passage text and store its vector under its id.
def add_vector(bank: MemoryBank, memory_id: int, subject: str, text: str) -> None:
    vector = bank.embedder.embed_passages([passage_text(subject, text)])[0]
    bank.vectors.add([memory_id], [vector])


# Save one fact under its subject and set the active memories in `replaces`
# inactive, pointing at the new one (only their vectors are removed). Returns
# (new memory id, ids actually replaced).
def save_memory(bank: MemoryBank, subject: str, text: str, language: str,
                now: datetime, replaces: Sequence[int] = ()) -> tuple[int, list[int]]:
    key = clean_subject(subject)
    if key is None or not text.strip():
        raise ValueError(f"bad memory: subject={subject!r}")
    stamp = now.isoformat(timespec="seconds")
    old = [int(r["id"]) for r in bank.conn.execute(
        f"SELECT id FROM memories WHERE active = 1 AND id IN ({','.join('?' * len(replaces))})",
        list(replaces)).fetchall()] if replaces else []
    with bank.conn:
        cur = bank.conn.execute(
            "INSERT INTO memories (subject, text, language, source, created_at, updated_at)"
            " VALUES (?, ?, ?, 'user', ?, ?)", (key, text.strip(), language, stamp, stamp))
        memory_id = int(cur.lastrowid)
        for old_id in old:
            bank.conn.execute("UPDATE memories SET active = 0, replaced_by = ?, updated_at = ?"
                              " WHERE id = ?", (memory_id, stamp, old_id))
    if old:
        bank.vectors.delete(old)
    add_vector(bank, memory_id, key, text)
    return memory_id, old


# The k memories nearest to a message vector, nearest first, with similarity.
def search_memories(bank: MemoryBank, vector: Sequence[float], k: int) -> list[Memory]:
    if bank.conn.execute("SELECT 1 FROM memories WHERE active = 1 LIMIT 1").fetchone() is None:
        return []
    found = []
    for memory_id, distance in bank.vectors.search(vector, k):
        row = bank.conn.execute("SELECT subject, text FROM memories WHERE id = ? AND active = 1",
                                (memory_id,)).fetchone()
        if row is not None:
            found.append(Memory(memory_id, row["subject"], row["text"], 1.0 - distance))
    return found


# The hints for the reply (M2.3b: no threshold): the recall_k nearest found memories.
def top_hints(found: list[Memory], cfg: MemoryConfig) -> list[Memory]:
    return found[: cfg.recall_k]


# All active memories, oldest first (for checks and, later, "what do you know about me?").
def all_memories(bank: MemoryBank) -> list[sqlite3.Row]:
    return bank.conn.execute("SELECT * FROM memories WHERE active = 1 ORDER BY id").fetchall()
