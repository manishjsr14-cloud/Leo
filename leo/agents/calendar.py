"""The calendar agent: see events, find free time, create, move, cancel (section 4.2).

Runs the shared step loop (leo/agents/loop.py) on mock calendar tools until
Radicale arrives in M2.6. Dates and times come from code, not the model:
read_calendar_times reads the user's latest message, the prompt shows the
exact values, and calendar_guard refuses any call that uses other ones.
When the words are unclear (e.g. "kal" with no tense) the agent asks the
user and makes no LLM call. Cancelling is 🔴: refused until approval (M2.5).
cancel_event is offered only when the message asks to cancel, and move_event
only when it asks to move or holds two times (leo/language/calendar_words.py).
Only the latest message is read, so a follow-up like "4 baje" alone is not
joined to the earlier request.
"""

from collections.abc import Callable
from datetime import datetime, timedelta

from langchain_core.messages import HumanMessage

from leo.agents.calendar_guard import guard_calendar_tools
from leo.agents.loop import agent_node, describe_tools, run_steps
from leo.config import CalendarConfig
from leo.graph.state import LeoState
from leo.language.calendar_words import asks_to_cancel, asks_to_move
from leo.language.time_parser import current_time
from leo.language.time_spans import CalendarTimes, read_calendar_times
from leo.ops import tracing
from leo.tools.base import Tool

NAME = "calendar"

# Kept here until versioned prompt files arrive in M1.8.
SYSTEM_PROMPT = (
    "You are Leo's calendar agent. You read and change the user's calendar, only "
    "through these tools:\n{tools}\n"
    'Reply only with JSON: either {{"tool": "<name>", "args": {{...}}}} to use one '
    'tool, or {{"done": true, "summary": "<what you did and the results>"}} when '
    "finished.\n"
    "Rules: never work out dates or times yourself; copy them exactly from 'Times "
    "from the user's words' below. Event ids come only from get_events results. "
    "Steps: to add an event, call create_event with the Event start and end. To "
    "move or cancel an event, first call get_events with a given range, then "
    "move_event or cancel_event with the id of the matching event from its result. "
    "To say what is on a day or whether the user is free, call get_events or "
    "find_free_slots with a given range. Then reply done. Cancelling needs the "
    "user's approval: if cancel_event is refused, do not retry it. A title is a few "
    "words from the user's message. Never repeat a tool call that already succeeded.\n"
    'Example: "Parso shaam 6 baje Neha ke saath call rakh do" -> create_event with '
    'title "Call with Neha" and the Event start and end below -> done.\n'
    "Today is {today}.\nTimes from the user's words:\n{times}\nYour task: {task}"
)

VERSION = tracing.prompt_version(SYSTEM_PROMPT)  # tags this agent's spans


# The exact times for the prompt, one per line.
def times_lines(times: CalendarTimes, event_minutes: int) -> str:
    lines = []
    if times.start is not None:
        end = times.start + timedelta(minutes=event_minutes)
        label = "New start for the moved event" if times.move_from else "Event"
        lines.append(f"- {label}: start {times.start.isoformat()}, end {end.isoformat()}")
    if times.move_from is not None:
        lines.append(f"- The event to move now starts at {times.move_from.isoformat()}")
    for name, span in (("part of the day", times.window), ("whole day", times.day)):
        if span is not None:
            lines.append(f"- Range for get_events or find_free_slots ({name}): "
                         f"start {span[0].isoformat()}, end {span[1].isoformat()}")
    return "\n".join(lines) or "- No date or time in the user's words."


# The tools offered for this message: cancel_event only when it asks to
# cancel, move_event only when it asks to move or holds two times.
def offered_tools(tools: dict[str, Tool], text: str, times: CalendarTimes) -> dict[str, Tool]:
    left_out = set()
    if not asks_to_cancel(text):
        left_out.add("cancel_event")
    if not (asks_to_move(text) or times.move_from is not None):
        left_out.add("move_event")
    return {name: tool for name, tool in tools.items() if name not in left_out}


# The text of the user's latest message ("" when there is none).
def latest_user_text(state: LeoState) -> str:
    users = [m for m in state.get("messages", []) if isinstance(m, HumanMessage)]
    return str(users[-1].content) if users else ""


# Run the agent for the supervisor's latest task, with `now` in IST.
# Returns {"steps": [...], "summary": str, "stopped": why}.
def run_agent(state: LeoState, chat: Callable, tools: dict[str, Tool], max_steps: int,
              now: datetime, config: CalendarConfig, force_cloud: bool = False) -> dict:
    text = latest_user_text(state)
    times = read_calendar_times(text, now, config)
    if times.status == "ask":
        return {"steps": [], "summary": times.question, "stopped": "ask"}
    guarded = guard_calendar_tools(offered_tools(tools, text, times), times,
                                   config.default_event_minutes)
    task = (state.get("plan") or [""])[-1]
    prompt = SYSTEM_PROMPT.format(tools=describe_tools(guarded), task=task,
                                  today=now.strftime("%A %d %B %Y, %H:%M"),
                                  times=times_lines(times, config.default_event_minutes))
    return run_steps(prompt, VERSION, state, chat, guarded, max_steps, force_cloud)


# Build the graph node for this agent. Its result goes in agent_results["calendar"].
# `now` gives the current IST time (a test or eval can fix it).
def calendar_agent(chat: Callable, tools: dict[str, Tool], max_steps: int,
                   config: CalendarConfig, now: Callable[[], datetime] = current_time,
                   ) -> Callable:
    return agent_node(NAME, lambda state, cloud: run_agent(state, chat, tools, max_steps,
                                                           now(), config, cloud))
