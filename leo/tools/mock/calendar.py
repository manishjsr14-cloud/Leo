"""Mock calendar tools for tests and evals. They never touch a real calendar.

Each tool works on a fixed list of events and appends a ToolCall to the call
log it was built with, so a test can check exactly which tools ran and with
what. Nothing is stored: create, move and cancel only return what they would do.
Tiers follow the section 9 table.
"""

import copy
from datetime import datetime

from leo.tools.base import Tier, Tool, ToolArgs, ToolCall, ToolError
from leo.tools.calendar_args import (
    CancelEventArgs,
    CreateEventArgs,
    FindFreeSlotsArgs,
    GetEventsArgs,
    MoveEventArgs,
)

# The fixed events, in IST: Monday 16 to Saturday 21 Nov 2026. Saturday's gym
# 8 am and call 10 am match the section 4.5 example.
FIXED_EVENTS = [
    {"id": "mock-evt-team", "title": "Team meeting",
     "start": "2026-11-16T15:00:00+05:30", "end": "2026-11-16T16:00:00+05:30"},
    {"id": "mock-evt-lunch", "title": "Lunch with Neha",
     "start": "2026-11-19T13:00:00+05:30", "end": "2026-11-19T14:00:00+05:30"},
    {"id": "mock-evt-gym", "title": "Gym",
     "start": "2026-11-21T08:00:00+05:30", "end": "2026-11-21T09:00:00+05:30"},
    {"id": "mock-evt-call", "title": "Call",
     "start": "2026-11-21T10:00:00+05:30", "end": "2026-11-21T10:30:00+05:30"},
]

# The id every mock create_event returns.
CREATED_EVENT_ID = "mock-evt-1"


# The events that overlap the range start..end, in start order.
def events_between(events: list[dict], start: datetime, end: datetime) -> list[dict]:
    found = [e for e in events if datetime.fromisoformat(e["start"]) < end
             and datetime.fromisoformat(e["end"]) > start]
    return sorted(copy.deepcopy(found), key=lambda e: datetime.fromisoformat(e["start"]))


# The free gaps inside start..end that no event covers, as {"start", "end"} dicts.
def free_gaps(events: list[dict], start: datetime, end: datetime) -> list[dict]:
    gaps, cursor = [], start
    for event in events_between(events, start, end):
        event_start = datetime.fromisoformat(event["start"])
        if event_start > cursor:
            gaps.append({"start": cursor.isoformat(), "end": event_start.isoformat()})
        cursor = max(cursor, datetime.fromisoformat(event["end"]))
    if cursor < end:
        gaps.append({"start": cursor.isoformat(), "end": end.isoformat()})
    return gaps


# Build the five mock calendar tools on `events` (FIXED_EVENTS unless given).
# Every call they make is appended to `log`.
def mock_calendar_tools(log: list[ToolCall], events: list[dict] | None = None) -> list[Tool]:
    events = copy.deepcopy(FIXED_EVENTS if events is None else events)

    # Add one call to the log, with the arguments as plain JSON values.
    def record(name: str, args: ToolArgs, result):
        log.append(ToolCall(tool=name, args=args.model_dump(mode="json"), result=result))
        return result

    # The events in the asked range (copies, so callers cannot change the originals).
    def get_events(args: GetEventsArgs) -> list[dict]:
        return record("get_events", args, events_between(events, args.start, args.end))

    # The free gaps in the asked range.
    def find_free_slots(args: FindFreeSlotsArgs) -> list[dict]:
        return record("find_free_slots", args, free_gaps(events, args.start, args.end))

    # Pretend to create an event and return it with the fixed id.
    def create_event(args: CreateEventArgs) -> dict:
        event = {"id": CREATED_EVENT_ID, **args.model_dump(mode="json")}
        return record("create_event", args, event)

    # Pretend to move a known event and return it with its new times.
    def move_event(args: MoveEventArgs) -> dict:
        event = next((e for e in events if e["id"] == args.event_id), None)
        if event is None:
            raise ToolError(f"no event with id {args.event_id!r}")
        moved = {**event, **args.model_dump(mode="json", exclude={"event_id"})}
        return record("move_event", args, moved)

    # Pretend to cancel an event and say which one.
    def cancel_event(args: CancelEventArgs) -> dict:
        return record("cancel_event", args, {"cancelled": args.event_id})

    specs = [
        ("get_events", "List calendar events between start and end.", Tier.SAFE,
         GetEventsArgs, get_events),
        ("find_free_slots", "List the free time between start and end.", Tier.SAFE,
         FindFreeSlotsArgs, find_free_slots),
        ("create_event", "Create a calendar event with a title, start and end.",
         Tier.NOTIFY, CreateEventArgs, create_event),
        ("move_event", "Move a calendar event (by its id) to a new start and end.",
         Tier.NOTIFY, MoveEventArgs, move_event),
        ("cancel_event", "Cancel a calendar event by its id.", Tier.CONFIRM,
         CancelEventArgs, cancel_event),
    ]
    return [Tool(name=n, description=d, tier=t, args_model=a, fn=f)
            for n, d, t, a, f in specs]
