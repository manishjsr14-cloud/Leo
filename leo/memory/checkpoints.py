"""LangGraph checkpoints in Leo's one database (M2.4, architecture sections 4.6 and 7).

The SqliteSaver writes through the same connection open_db returns, so the
checkpoint tables (`checkpoints`, `writes`) sit in the one SQLite file next to
`memories` and there is still one writer. Each conversation is one thread_id;
the graph saves its state after every step, so a conversation continues after
the CLI is killed and started again.

What a checkpoint keeps: the messages (older ones folded into `summary`) and
the other state fields. A turn killed halfway leaves the user's message in the
thread with no reply (docs/known_limits.md).

Pending offer (designed here, built in M2.5): a code-written offer such as
"Sat 29 Nov — kya main ise calendar mein daal doon?" would be kept in the state
field `pending_offer` = {kind: "calendar_event", text, date, time, part_of_day,
language, offered_at}, set by the responder with the offer, saved in this
checkpoint, and cleared at the start of the next turn unless that turn is an
acceptance ("haan", "yes", "daal do"), which M2.5 turns into a calendar request
through approval. Because it is in the checkpoint, "haan" works after a restart.
"""

import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver


# A checkpointer on `conn` (a connection from leo.memory.store.open_db); creates
# its tables on first use.
def open_checkpointer(conn: sqlite3.Connection) -> SqliteSaver:
    saver = SqliteSaver(conn)
    saver.setup()
    return saver


# The thread's saved state values ({} when the thread has no checkpoint).
def thread_values(saver: SqliteSaver, thread_id: str) -> dict:
    saved = saver.get_tuple({"configurable": {"thread_id": thread_id}})
    return dict(saved.checkpoint["channel_values"]) if saved else {}
