"""Memory history: replaced memories are kept, and a wrong replacement can be undone
(M2.3 fix round).

In the M2.3 check the extraction step gave "Meri behen ka birthday 12 March ko
hai" the subject of the sister's NAME, so the name was replaced by the
birthday. Since then a replaced memory stays in `memories` as inactive history
(active = 0, replaced_by = the memory that replaced it), and undo_replacement
brings it back; the replacing memory can move to its own subject or be set
inactive. Nothing here is called by the graph yet ("Leo, forget that" and
"undo" in chat come later, section 14.7).
"""

import sqlite3
from datetime import datetime

from leo.memory.memories import MemoryBank, add_vector, clean_subject


# Every memory ever stored on a subject, active or not, oldest first.
def history(bank: MemoryBank, subject: str) -> list[sqlite3.Row]:
    return bank.conn.execute("SELECT * FROM memories WHERE subject = ? ORDER BY id",
                             (subject,)).fetchall()


# Undo the replacement made by memory `memory_id`: the memory it replaced is
# active again. The replacing memory moves to `new_subject` (when given, it stays
# active there) or becomes inactive. Returns the restored memory's id.
def undo_replacement(bank: MemoryBank, memory_id: int, now: datetime,
                     new_subject: str | None = None) -> int:
    new = bank.conn.execute("SELECT * FROM memories WHERE id = ? AND active = 1",
                            (memory_id,)).fetchone()
    old = bank.conn.execute("SELECT * FROM memories WHERE replaced_by = ?",
                            (memory_id,)).fetchone()
    if new is None or old is None:
        raise ValueError(f"memory {memory_id} is not an active replacement")
    key = clean_subject(new_subject) if new_subject else None
    if new_subject and key is None:
        raise ValueError(f"bad subject: {new_subject!r}")
    stamp = now.isoformat(timespec="seconds")
    with bank.conn:
        if key is None:
            bank.conn.execute("UPDATE memories SET active = 0, updated_at = ? WHERE id = ?",
                              (stamp, memory_id))
        else:
            bank.conn.execute("UPDATE memories SET subject = ?, updated_at = ? WHERE id = ?",
                              (key, stamp, memory_id))
        bank.conn.execute("UPDATE memories SET active = 1, replaced_by = NULL, updated_at = ?"
                          " WHERE id = ?", (stamp, old["id"]))
    bank.vectors.delete([memory_id])
    if key is not None:
        add_vector(bank, memory_id, key, new["text"])
    add_vector(bank, int(old["id"]), old["subject"], old["text"])
    return int(old["id"])
