-- Leo's SQLite tables (architecture section 7). Applied by leo/memory/store.py.
-- Only the tables used so far; later tasks add theirs here.
-- Times are ISO 8601 text with the time zone, for example 2026-11-13T18:05:00+05:30.

CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY,
    title      TEXT    NOT NULL CHECK (length(title) > 0),
    done       INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)),
    created_at TEXT    NOT NULL,
    done_at    TEXT
);

CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY,
    text       TEXT    NOT NULL CHECK (length(text) > 0),
    created_at TEXT    NOT NULL
);

-- Long-term memory (M2.3, section 7): one ACTIVE lasting fact or preference per
-- subject, in the user's own words. A new fact on the same subject replaces the old
-- one, which is kept as inactive history (active = 0, replaced_by = the new id), so
-- a wrong replacement can be undone (M2.3 fix round).
-- Only the user's own messages become memories (section 14.7): source is always 'user'.
-- The vectors of active memories are in the vec0 table vec_memories (rowid = memories.id).
CREATE TABLE IF NOT EXISTS memories (
    id          INTEGER PRIMARY KEY,
    subject     TEXT    NOT NULL CHECK (length(subject) > 0),
    text        TEXT    NOT NULL CHECK (length(text) > 0),
    language    TEXT    NOT NULL,
    source      TEXT    NOT NULL DEFAULT 'user' CHECK (source = 'user'),
    active      INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    replaced_by INTEGER REFERENCES memories (id),
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS memories_one_active_subject
    ON memories (subject) WHERE active = 1;
