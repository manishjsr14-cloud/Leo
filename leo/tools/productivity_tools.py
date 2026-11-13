"""Names, descriptions and tiers of the 7 productivity tools (section 9: all 🟢).

The real and mock versions use this one list, so they can never drift apart.
"""

from leo.tools.base import Tier, Tool
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
    "complete_task": ("Mark a task done by its id from list_tasks.", CompleteTaskArgs),
    "add_note": ("Save a note.", AddNoteArgs),
    "list_notes": ("List the newest notes.", ListNotesArgs),
    "start_timer": ("Start a countdown timer for some minutes, with a label.", StartTimerArgs),
    "calculate": (
        ("Work out arithmetic. Copy the user's expression exactly, e.g. "
         "'18% of 2450'. Never compute it yourself."),
        CalculateArgs,
    ),
}


# Turn a name -> function dict into Tool objects, all 🟢 SAFE.
def make_tools(functions: dict) -> list[Tool]:
    if set(functions) != set(SPECS):
        raise ValueError(f"functions must be exactly {sorted(SPECS)}")
    return [
        Tool(name=name, description=description, tier=Tier.SAFE, args_model=args_model,
             fn=functions[name])
        for name, (description, args_model) in SPECS.items()
    ]
