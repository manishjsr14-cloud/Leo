"""The calendar agent: see events, find free time, create, move, cancel (section 4.2).

Runs the shared step loop (leo/agents/loop.py) on mock calendar tools until
Radicale arrives in M2.6. Dates and times come from code, not the model:
read_calendar_times reads the user's latest message, calendar_fill adds the
exact times to every call (the model gives only a title, an event id or a
range name), and calendar_guard checks each filled call again.
When the words are unclear (e.g. "kal" with no tense) the agent asks the
user and makes no LLM call. Cancelling is 🔴: refused until approval (M2.5).
cancel_event is offered only when the message asks to cancel, and move_event
only when it asks to move or holds two times (leo/language/calendar_words.py).
Two times mean a move: create_event is then not offered, and with a create
word as well ("3 se 5 baje tak workshop add karo") the agent asks instead.
Only the latest message is read, so a follow-up like "4 baje" alone is not
joined to the earlier request.
M1.8: the prompt is prompts/calendar.yaml; a single create or move, or a read
when nothing is to change, ends the run in code (leo/agents/finish.py); free
time is looked for in waking hours only; the result says whether the am/pm
of the time was assumed, so the reply can ask about it.
"""

from collections.abc import Callable
from datetime import datetime, timedelta

from leo.agents.calendar_fill import (
    Range,
    fill_calendar_tools,
    named_ranges,
    waking_ranges,
)
from leo.agents.calendar_guard import guard_calendar_tools
from leo.agents.finish import finish_rule
from leo.agents.loop import agent_node, describe_tools, run_steps
from leo.config import CalendarConfig
from leo.graph.state import LeoState, latest_user_text
from leo.language.calendar_words import (
    ADD_OR_MOVE,
    asks_to_cancel,
    asks_to_create,
    asks_to_move,
)
from leo.language.say_time import say_clock, say_day, say_span
from leo.language.time_parser import current_time
from leo.language.time_spans import CalendarTimes, read_calendar_times
from leo.llm.prompts import load_prompt
from leo.tools.base import Tool

NAME = "calendar"
PROMPT = load_prompt("calendar")  # prompts/calendar.yaml
VERSION = PROMPT.tag              # tags this agent's spans
# A run ends in code after one of these succeeds (not cancel: "clear" may need several).
ENDS_RUN = {"create_event", "move_event"}
READS = {"get_events", "find_free_slots"}


# The times and range names for the prompt, written out, one per line.
def times_lines(times: CalendarTimes, ranges: dict[str, Range], event_minutes: int) -> str:
    lines = []
    if times.start is not None:
        span = say_span(times.start, times.start + timedelta(minutes=event_minutes))
        label = "New time for the moved event" if times.move_from else "Event time"
        lines.append(f"- {label}: {span}")
    else:
        lines.append("- No event time in the user's words.")
    if times.move_from is not None:
        lines.append(f"- The event to move now starts: {say_day(times.move_from)}, "
                     f"{say_clock(times.move_from)}")
    lines += [f'- range "{name}": {say_span(*span)}' for name, span in ranges.items()]
    return "\n".join(lines)


# The tools offered for this message: cancel_event only when it asks to
# cancel, move_event only when it asks to move or holds two times, and no
# create_event when it holds two times.
def offered_tools(tools: dict[str, Tool], text: str, times: CalendarTimes) -> dict[str, Tool]:
    left_out = {"create_event"} if times.move_from is not None else set()
    if not asks_to_cancel(text):
        left_out.add("cancel_event")
    if not (asks_to_move(text) or times.move_from is not None):
        left_out.add("move_event")
    return {name: tool for name, tool in tools.items() if name not in left_out}


# True when the message asks to add, move or cancel (a read then does not end the run).
def asks_change(text: str, times: CalendarTimes) -> bool:
    return (asks_to_create(text) or asks_to_move(text) or asks_to_cancel(text)
            or times.move_from is not None)


# Run the agent for the supervisor's latest task, with `now` in IST.
# Returns {"steps": [...], "summary": str, "stopped": why, "assumed_ampm": bool,
# "today": ISO date the responder uses for "tomorrow" etc.}.
def run_agent(state: LeoState, chat: Callable, tools: dict[str, Tool], max_steps: int,
              now: datetime, config: CalendarConfig, force_cloud: bool = False) -> dict:
    text = latest_user_text(state)
    times = read_calendar_times(text, now, config)
    if times.status == "ask":
        return {"steps": [], "summary": times.question, "stopped": "ask"}
    if times.move_from is not None and asks_to_create(text):
        return {"steps": [], "summary": ADD_OR_MOVE, "stopped": "ask"}
    minutes, ranges = config.default_event_minutes, named_ranges(times, now)
    free, seen = waking_ranges(ranges, config.waking_hours), {}  # seen: events listed
    guarded = guard_calendar_tools(offered_tools(tools, text, times), times, minutes,
                                   ranges, free, seen)
    filled = fill_calendar_tools(guarded, times, ranges, minutes, free, seen)
    task = (state.get("plan") or [""])[-1]
    prompt = PROMPT.render(tools=describe_tools(filled), task=task,
                           today=now.strftime("%A %d %B %Y, %H:%M"),
                           times=times_lines(times, ranges, minutes))
    finish = finish_rule(text, ENDS_RUN, READS, asks_change(text, times))
    out = run_steps(prompt, VERSION, state, chat, filled, max_steps, force_cloud, finish)
    return {**out, "assumed_ampm": times.assumed_ampm, "today": now.date().isoformat()}


# Build the graph node for this agent. Its result goes in agent_results["calendar"].
# `now` gives the current IST time (a test or eval can fix it).
def calendar_agent(chat: Callable, tools: dict[str, Tool], max_steps: int,
                   config: CalendarConfig, now: Callable[[], datetime] = current_time,
                   ) -> Callable:
    return agent_node(NAME, lambda state, cloud: run_agent(state, chat, tools, max_steps,
                                                           now(), config, cloud))
