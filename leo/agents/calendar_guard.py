"""Checks that hold the calendar agent to the times worked out in code (M1.7).

The model never decides a date or time. Before a calendar tool runs:
  - get_events / find_free_slots: the range must be exactly one of the named
    ranges code offered (calendar_fill.named_ranges), or without those the
    part-of-day window or the whole day taken from the user's words;
  - create_event: start must be exactly the parsed time, end start + the
    default length (calendar.default_event_minutes);
  - move_event: the same for the new time, and the event must be one that
    get_events returned in this run whose current start is the FIRST time in
    the user's words;
  - cancel_event: the id must be one get_events returned in this run. This
    check runs before the approval check, so an invented id is refused as
    such; a real id is then still refused for approval until M2.5.
The checks are set as each tool's `check`, which call_tool runs first, so a
refused call never reaches the calendar and nothing is logged. With no date
or time to check against, the tool asks the user instead (AskUser).
"""

from collections.abc import Callable
from datetime import datetime, timedelta

from leo.language.time_spans import CalendarTimes
from leo.tools.base import AskUser, Tool, ToolError

# Questions asked back (Hinglish; prompts move to prompts/ in M1.8).
ASK_TIME = "Kis time pe?"
ASK_DAY = "Kis din ka?"
ASK_DAY_TIME = "Kis din aur kis time pe?"
ASK_MOVE = "Meeting abhi kis time pe hai, aur kis time pe le jaani hai?"


# Copies of the calendar tools whose functions first run the checks above.
def guard_calendar_tools(tools: dict[str, Tool], times: CalendarTimes, event_minutes: int,
                         ranges: dict[str, tuple[datetime, datetime]] | None = None,
                         ) -> dict[str, Tool]:
    length = timedelta(minutes=event_minutes)
    seen: dict[str, datetime] = {}  # event id -> current start, from get_events

    # Refuse a range that is not one of the allowed ranges.
    def check_range(args) -> None:
        if ranges is not None:
            allowed = list(ranges.values())
        elif times.day is None:
            raise AskUser(ASK_DAY)
        else:
            allowed = [r for r in (times.window, times.day) if r is not None]
        if (args.start, args.end) not in allowed:
            text = " or ".join(f"{a.isoformat()} to {b.isoformat()}" for a, b in allowed)
            raise ToolError(f"use exactly this range: {text}")

    # Refuse a start or end that is not the parsed time and the default end.
    def check_start(args) -> None:
        if times.start is None:
            raise AskUser(ASK_TIME if times.day is not None else ASK_DAY_TIME)
        if args.start != times.start or args.end != times.start + length:
            raise ToolError(f"use exactly start {times.start.isoformat()} and end "
                            f"{(times.start + length).isoformat()}")

    # Refuse a move unless the event was listed and starts at the first time.
    def check_move(args) -> None:
        if times.move_from is None:
            raise AskUser(ASK_MOVE)
        check_start(args)
        current = seen.get(args.event_id)
        if current is None:
            raise ToolError("call get_events first and use an event id from its result")
        if current != times.move_from:
            raise ToolError(f"event {args.event_id} starts at {current.isoformat()}, not at "
                            f"{times.move_from.isoformat()}; pick the event starting then")

    # Refuse a cancel of an event get_events did not list in this run.
    def check_cancel(args) -> None:
        if args.event_id not in seen:
            raise ToolError("call get_events first and use an event id from its result")

    # get_events also remembers each listed event's start for check_move.
    def remember(result: list[dict]) -> None:
        for event in result:
            seen[event["id"]] = datetime.fromisoformat(event["start"])

    checks: dict[str, tuple[Callable, Callable | None]] = {
        "get_events": (check_range, remember),
        "find_free_slots": (check_range, None),
        "create_event": (check_start, None),
        "move_event": (check_move, None),
        "cancel_event": (check_cancel, None),
    }

    # Set the tool's check, and wrap its function when it has an after-step.
    def wrap(tool: Tool, check: Callable, after: Callable | None) -> Tool:
        if after is None:
            return tool.model_copy(update={"check": check})

        # Run the real function, then the after-step on its result.
        def run(args):
            result = tool.fn(args)
            after(result)
            return result
        return tool.model_copy(update={"check": check, "fn": run})

    return {name: wrap(tool, *checks[name]) if name in checks else tool
            for name, tool in tools.items()}
