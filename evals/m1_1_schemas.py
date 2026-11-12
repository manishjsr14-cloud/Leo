"""Pydantic schemas used by the fixed M1.1 model check set.

Committed together with evals/scenarios/m1_1_schema_check.yaml and never
edited afterwards; a better version is a new file.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class AgentChoice(BaseModel):
    """Which agent should handle the request, and the task for it."""

    next: Literal["calendar", "research", "productivity", "responder"]
    task: str = Field(min_length=1)


class EventDetails(BaseModel):
    """An event pulled out of a request: title, date and optional 24-hour time."""

    title: str = Field(min_length=1)
    date: date
    time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


SCHEMAS = {"AgentChoice": AgentChoice, "EventDetails": EventDetails}
