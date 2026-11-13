"""Argument schemas for the productivity tools (architecture sections 9 and 12.3).

Shared by the real SQLite tools and the mock tools. Unknown keys are refused
(ToolArgs uses extra="forbid").
"""

from pydantic import Field, model_validator

from leo.tools.base import ToolArgs


class AddTaskArgs(ToolArgs):
    """Arguments for add_task: the task's title, e.g. "milk"."""

    title: str = Field(min_length=1, max_length=200)


class ListTasksArgs(ToolArgs):
    """Arguments for list_tasks: whether to include tasks already done."""

    include_done: bool = False


class CompleteTaskArgs(ToolArgs):
    """Arguments for complete_task: exactly one of task_id or title."""

    task_id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)

    # Reject both or neither: the task is chosen by id or by title, never both.
    @model_validator(mode="after")
    def exactly_one(self):
        if (self.task_id is None) == (self.title is None):
            raise ValueError("give exactly one of task_id or title")
        return self


class AddNoteArgs(ToolArgs):
    """Arguments for add_note: the note's text."""

    text: str = Field(min_length=1, max_length=2000)


class ListNotesArgs(ToolArgs):
    """Arguments for list_notes: how many of the newest notes to return."""

    limit: int = Field(default=10, ge=1, le=50)


class StartTimerArgs(ToolArgs):
    """Arguments for start_timer: length in minutes (up to one day) and a label."""

    minutes: float = Field(gt=0, le=1440)
    label: str = Field(default="timer", min_length=1, max_length=100)


class CalculateArgs(ToolArgs):
    """Arguments for calculate: the user's expression, copied as written."""

    expression: str = Field(min_length=1, max_length=200)
