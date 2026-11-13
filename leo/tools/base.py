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


class ToolCall(BaseModel):
    """One recorded call: which tool, the checked arguments, and what it returned."""

    tool: str
    args: dict[str, Any]
    result: Any
