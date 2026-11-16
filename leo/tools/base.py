"""Building blocks for Leo's tools (architecture sections 9 and 12.3).

A tool is a plain function plus a Pydantic schema for its arguments and a
safety tier. registry.call_tool checks the arguments and the tier before the
function runs, so the function itself always gets clean, checked input.
"""

from collections.abc import Callable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class Tier(StrEnum):
    """How risky a tool is (section 9)."""

    SAFE = "safe"  # 🟢 runs straight away
    NOTIFY = "notify"  # 🟡 runs, and the user is told (undo comes in a later task)
    CONFIRM = "confirm"  # 🔴 runs only after human approval


class ToolError(Exception):
    """A tool could not do what was asked (for example, no task with that id).

    The message is short and safe to show the model, so it can try again.
    """


class AskUser(ToolError):
    """The tool needs something only the user can give, such as a time.

    The message is the question for the user, written by Leo's code (never the model).
    """


class ToolArgs(BaseModel):
    """Base for every tool's argument schema.

    Unknown keys are an error, so a typo or an unexpected key from the model
    (for example "approved") is rejected instead of silently dropped.
    """

    model_config = ConfigDict(extra="forbid")


class Tool(BaseModel):
    """One tool: its name, what it does, its tier, its argument schema and its function."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    tier: Tier
    args_model: type[ToolArgs]
    fn: Callable[[Any], Any]
    # Optional extra check on the checked arguments, run by call_tool before the
    # approval check; it raises ToolError (or AskUser) to refuse the call.
    check: Callable[[Any], None] | None = None
    # Optional: the smaller schema the MODEL fills in instead of args_model, and
    # how code turns the model's arguments into the full ones (e.g. the calendar
    # agent adds the exact start and end, so the model never writes a date).
    model_args: type[ToolArgs] | None = None
    fill: Callable[[dict], dict] | None = None


class ToolCall(BaseModel):
    """One recorded call: which tool, the checked arguments, and what it returned."""

    tool: str
    args: dict[str, Any]
    result: Any


# Checked arguments as plain JSON values, leaving out unset optional ones (None),
# e.g. complete_task by id gives {"task_id": 1}, not {"task_id": 1, "title": None}.
def plain(args: ToolArgs) -> dict[str, Any]:
    return args.model_dump(mode="json", exclude_none=True)
