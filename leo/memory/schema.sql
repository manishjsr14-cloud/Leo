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
