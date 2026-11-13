"""Argument schemas for the calendar tools (architecture sections 9 and 12.3).

Shared by the mock calendar now and the real Radicale calendar later (M2).
All times must carry a time zone, and an end must come after its start.
"""

from pydantic import AwareDatetime, Field, model_validator

from leo.tools.base import ToolArgs


class TimeRange(ToolArgs):
    """A start and end time, both with a time zone, end after start."""

    start: AwareDatetime
    end: AwareDatetime

    # Reject a range whose end is not after its start.
    @model_validator(mode="after")
    def end_after_start(self):
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self


class GetEventsArgs(TimeRange):
    """Arguments for get_events: the time range to look at."""


class CreateEventArgs(TimeRange):
    """Arguments for create_event: a title plus the event's start and end."""

    title: str = Field(min_length=1)


class CancelEventArgs(ToolArgs):
    """Arguments for cancel_event: the id of the event to cancel."""

    event_id: str = Field(min_length=1)
