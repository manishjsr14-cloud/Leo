"""Mock calendar tools for tests and evals. They never touch a real calendar.

Each tool returns fixed data and appends a ToolCall to the call log it was
built with, so a test can check exactly which tools ran and with what.
Tiers follow the section 9 table.
"""

import copy

from leo.tools.base import Tier, Tool, ToolArgs, ToolCall
from leo.tools.calendar_args import CancelEventArgs, CreateEventArgs, GetEventsArgs

# Two fixed events on Saturday 14 Nov 2026, in IST. get_events always
# returns these, whatever range is asked for.
FIXED_EVENTS = [
    {
        "id": "mock-evt-gym",
        "title": "Gym",
        "start": "2026-11-14T08:00:00+05:30",
        "end": "2026-11-14T09:00:00+05:30",
    },
    {
        "id": "mock-evt-call",
        "title": "Call with Rahul",
        "start": "2026-11-14T10:00:00+05:30",
        "end": "2026-11-14T10:30:00+05:30",
    },
]

# The id every mock create_event returns.
CREATED_EVENT_ID = "mock-evt-1"


# Build the three mock calendar tools. Every call they make is appended to `log`.
def mock_calendar_tools(log: list[ToolCall]) -> list[Tool]:
    # Add one call to the log, with the arguments as plain JSON values.
    def record(name: str, args: ToolArgs, result):
        log.append(ToolCall(tool=name, args=args.model_dump(mode="json"), result=result))
        return result

    # Return the fixed events (a copy, so callers cannot change the originals).
    def get_events(args: GetEventsArgs) -> list[dict]:
        return record("get_events", args, copy.deepcopy(FIXED_EVENTS))

    # Pretend to create an event and return it with the fixed id.
    def create_event(args: CreateEventArgs) -> dict:
        event = {"id": CREATED_EVENT_ID, **args.model_dump(mode="json")}
        return record("create_event", args, event)

    # Pretend to cancel an event and say which one.
    def cancel_event(args: CancelEventArgs) -> dict:
        return record("cancel_event", args, {"cancelled": args.event_id})

    return [
        Tool(
            name="get_events",
            description="List calendar events between start and end.",
            tier=Tier.SAFE,
            args_model=GetEventsArgs,
            fn=get_events,
        ),
        Tool(
            name="create_event",
            description="Create a calendar event with a title, start and end.",
            tier=Tier.NOTIFY,
            args_model=CreateEventArgs,
            fn=create_event,
        ),
        Tool(
            name="cancel_event",
            description="Cancel a calendar event by its id.",
            tier=Tier.CONFIRM,
            args_model=CancelEventArgs,
            fn=cancel_event,
        ),
    ]
