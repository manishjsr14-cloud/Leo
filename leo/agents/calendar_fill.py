"""Code fills in every date and time for the calendar agent (M1.7 run4).

The model never writes a date. It fills in only:
  - create_event: {"title": ...}            -> code adds the parsed start and end
  - move_event:   {"event_id": ...}         -> code adds the new start and end
  - get_events / find_free_slots: {"range": "<name>"} -> code adds that range
Range names: "window" (part of the day, when the words name one) and "day"
(the whole day the words name); with no date in the words, "today" and
"next_7_days". The guard (calendar_guard.py) still checks the filled call.
find_free_slots gets the same ranges cut to calendar.waking_hours (M1.8), so
"free on Saturday?" is not answered with 00:00-08:00; get_events keeps the
whole day, so no event is missed.
"""

from datetime import datetime, time, timedelta
from typing import Literal

from pydantic import Field, create_model

from leo.agents.calendar_guard import ASK_DAY_TIME, ASK_MOVE, ASK_TIME
from leo.language.time_spans import CalendarTimes
from leo.tools.base import AskUser, Tool, ToolArgs, ToolError

Range = tuple[datetime, datetime]


class TitleArgs(ToolArgs):
    """What the model gives for create_event: only the title."""

    title: str = Field(min_length=1)


class EventIdArgs(ToolArgs):
    """What the model gives for move_event: only the event's id."""

    event_id: str = Field(min_length=1)


# The named ranges offered for get_events and find_free_slots.
def named_ranges(times: CalendarTimes, now: datetime) -> dict[str, Range]:
    if times.day is None:
        today = datetime.combine(now.date(), time(0), now.tzinfo)
        return {"today": (today, today + timedelta(days=1)),
                "next_7_days": (today, today + timedelta(days=7))}
    window = {"window": times.window} if times.window is not None else {}
    return {**window, "day": times.day}


# The ranges cut to waking hours, for find_free_slots (M1.8): a range that
# starts at midnight starts at the first waking hour, and one that ends at
# midnight ends at the last. Nights inside a range of several days stay in.
def waking_ranges(ranges: dict[str, Range], waking: tuple[int, int]) -> dict[str, Range]:
    first, last = timedelta(hours=waking[0]), timedelta(hours=24 - waking[1])
    cut = {}
    for name, (start, end) in ranges.items():
        start = start + first if start.time() == time(0) else start
        end = end - last if end.time() == time(0) else end
        cut[name] = (start, end)
    return cut


# Copies of the tools with the model's smaller schema and the code fill.
# find_free_slots uses `free_ranges` (the waking-hours cut) when given.
def fill_calendar_tools(tools: dict[str, Tool], times: CalendarTimes,
                        ranges: dict[str, Range], event_minutes: int,
                        free_ranges: dict[str, Range] | None = None) -> dict[str, Tool]:
    length = timedelta(minutes=event_minutes)
    range_args = create_model("RangeArgs", __base__=ToolArgs,
                              range=(Literal[tuple(ranges)], ...))  # type: ignore[valid-type]

    # A fill that gives the start and end of the named range, as ISO text.
    def range_fill(named: dict[str, Range]):
        # Start and end of the named range.
        def by_range(args: dict) -> dict:
            if args.get("range") not in named:
                raise ToolError(f"range must be one of {list(named)}")
            start, end = named[args["range"]]
            return {"start": start.isoformat(), "end": end.isoformat()}
        return by_range

    # The parsed start and the default end, or a question when there is no time.
    def event_times() -> dict:
        if times.start is None:
            raise AskUser(ASK_TIME if times.day is not None else ASK_DAY_TIME)
        return {"start": times.start.isoformat(), "end": (times.start + length).isoformat()}

    # create_event: the model's title plus the code's times.
    def create(args: dict) -> dict:
        return {"title": args.get("title"), **event_times()}

    # move_event: the model's event id plus the code's new times.
    def move(args: dict) -> dict:
        if times.move_from is None:
            raise AskUser(ASK_MOVE)
        return {"event_id": args.get("event_id"), **event_times()}

    fills = {"get_events": (range_args, range_fill(ranges)),
             "find_free_slots": (range_args, range_fill(free_ranges or ranges)),
             "create_event": (TitleArgs, create), "move_event": (EventIdArgs, move)}
    return {name: tool.model_copy(update={"model_args": fills[name][0], "fill": fills[name][1]})
            if name in fills else tool for name, tool in tools.items()}
