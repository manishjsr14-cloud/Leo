"""Real productivity tools: tasks and notes in SQLite, timer, calculator.

Built around one open database connection (leo/memory/store.py). Tests pass a
temporary database; only the CLI and server open the real one in leo_data/.
A timer only computes its end time here; `schedule` (from the CLI) makes it
ring. Saved timers that survive a restart come with the scheduler in M2.7.
"""

import sqlite3
from collections.abc import Callable
from datetime import datetime, timedelta

from leo.tools.base import Tool, ToolError
from leo.tools.calculator import CalculatorError, calculate
from leo.tools.productivity_args import (
    AddNoteArgs,
    AddTaskArgs,
    CalculateArgs,
    CompleteTaskArgs,
    ListNotesArgs,
    ListTasksArgs,
    StartTimerArgs,
)
from leo.tools.productivity_tools import make_tools


# The current time with the laptop's time zone (IST on Leo's laptop).
def local_now() -> datetime:
    return datetime.now().astimezone()


# One task row as a plain dict for the model.
def _task(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


# Build the 7 tools on `conn`. schedule(seconds, label) is called by start_timer
# so the caller can ring the timer; `now` can be swapped in tests.
def real_productivity_tools(
    conn: sqlite3.Connection,
    schedule: Callable[[float, str], None] | None = None,
    now: Callable[[], datetime] = local_now,
) -> list[Tool]:
    # Insert a new open task and return it.
    def add_task(args: AddTaskArgs) -> dict:
        cur = conn.execute("INSERT INTO tasks (title, created_at) VALUES (?, ?)",
                           (args.title, now().isoformat()))
        conn.commit()
        return {"id": cur.lastrowid, "title": args.title, "done": False}

    # Return tasks, oldest first; open ones only unless include_done.
    def list_tasks(args: ListTasksArgs) -> list[dict]:
        where = "" if args.include_done else "WHERE done = 0"
        rows = conn.execute(f"SELECT id, title, done FROM tasks {where} ORDER BY id")
        return [_task(r) for r in rows]

    # Mark one task done. Raises ToolError if the id does not exist.
    def complete_task(args: CompleteTaskArgs) -> dict:
        row = conn.execute("SELECT id, title, done FROM tasks WHERE id = ?",
                           (args.task_id,)).fetchone()
        if row is None:
            raise ToolError(f"no task with id {args.task_id}; use list_tasks for ids")
        if not row["done"]:
            conn.execute("UPDATE tasks SET done = 1, done_at = ? WHERE id = ?",
                         (now().isoformat(), args.task_id))
            conn.commit()
        return {"id": row["id"], "title": row["title"], "done": True}

    # Save a note and return it.
    def add_note(args: AddNoteArgs) -> dict:
        cur = conn.execute("INSERT INTO notes (text, created_at) VALUES (?, ?)",
                           (args.text, now().isoformat()))
        conn.commit()
        return {"id": cur.lastrowid, "text": args.text}

    # Return the newest notes first.
    def list_notes(args: ListNotesArgs) -> list[dict]:
        rows = conn.execute("SELECT id, text FROM notes ORDER BY id DESC LIMIT ?",
                            (args.limit,))
        return [{"id": r["id"], "text": r["text"]} for r in rows]

    # Work out the end time and ask `schedule` to ring the timer.
    def start_timer(args: StartTimerArgs) -> dict:
        ends_at = now() + timedelta(minutes=args.minutes)
        if schedule is not None:
            schedule(args.minutes * 60, args.label)
        return {"label": args.label, "minutes": args.minutes,
                "ends_at": ends_at.isoformat(timespec="seconds")}

    # Let sympy work out the expression (never the LLM).
    def calculate_tool(args: CalculateArgs) -> dict:
        try:
            return calculate(args.expression)
        except CalculatorError as error:
            raise ToolError(str(error)) from error

    return make_tools({
        "add_task": add_task, "list_tasks": list_tasks, "complete_task": complete_task,
        "add_note": add_note, "list_notes": list_notes, "start_timer": start_timer,
        "calculate": calculate_tool,
    })
