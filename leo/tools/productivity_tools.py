"""Names, descriptions and tiers of the 7 productivity tools (section 9: all 🟢).

The real and mock versions use this one list, so they can never drift apart.
"""

from leo.tools.base import Tier, Tool, ToolError
from leo.tools.productivity_args import (
    AddNoteArgs,
    AddTaskArgs,
    CalculateArgs,
    CompleteTaskArgs,
    ListNotesArgs,
    ListTasksArgs,
    StartTimerArgs,
)

# name -> (description, argument schema)
SPECS = {
    "add_task": ("Add a to-do task with a short title.", AddTaskArgs),
    "list_tasks": ("List to-do tasks with their ids (open ones unless include_done).",
                   ListTasksArgs),
    "complete_task": ("Mark one open task done, by its title (e.g. 'milk') or its id.",
                      CompleteTaskArgs),
    "add_note": ("Save a note.", AddNoteArgs),
    "list_notes": ("List the newest notes.", ListNotesArgs),
    "start_timer": ("Start a countdown timer for some minutes, with a label.", StartTimerArgs),
    "calculate": (
        ("Work out arithmetic. Copy the user's expression exactly, e.g. "
         "'18% of 2450'. Never compute it yourself."),
        CalculateArgs,
    ),
}


# Find the one open task whose title contains `title` (case-insensitive).
# `tasks` are dicts with id, title and done. Errors (ToolError) list the
# candidates with their ids so the agent can ask the user:
# more than one open match, only done matches ("already done"), or no match.
def pick_task_by_title(tasks: list[dict], title: str) -> dict:
    wanted = title.strip().casefold()
    matches = [t for t in tasks if wanted in t["title"].casefold()]
    open_matches = [t for t in matches if not t["done"]]

    # Only id and title, for the error messages.
    def ids(rows):
        return [{"id": t["id"], "title": t["title"]} for t in rows]

    if len(open_matches) == 1:
        return open_matches[0]
    if open_matches:
        raise ToolError(f"{len(open_matches)} open tasks match {title!r}: "
                        f"{ids(open_matches)}; ask the user which one")
    if matches:
        raise ToolError(f"task {title!r} is already done: {ids(matches)}")
    open_tasks = [t for t in tasks if not t["done"]]
    raise ToolError(f"no open task matches {title!r}; open tasks: {ids(open_tasks)}")


# Turn a name -> function dict into Tool objects, all 🟢 SAFE.
def make_tools(functions: dict) -> list[Tool]:
    if set(functions) != set(SPECS):
        raise ValueError(f"functions must be exactly {sorted(SPECS)}")
    return [
        Tool(name=name, description=description, tier=Tier.SAFE, args_model=args_model,
             fn=functions[name])
        for name, (description, args_model) in SPECS.items()
    ]
