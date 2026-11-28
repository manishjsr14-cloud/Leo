"""The real graph the CLI chats with (split out of leo/cli.py to keep it short).

The productivity agent keeps tasks and notes in leo_data/leo.db; the research
agent uses DuckDuckGo, web pages and Open-Meteo over the internet. The calendar
agent uses the MOCK calendar (fixed events, nothing saved) until M2.6.
Long-term memory (M2.3) and the conversation checkpoints (M2.4) are in the
same database, written through its one connection.
"""

import threading
from collections.abc import Callable

from leo.agents.calendar import calendar_agent
from leo.agents.productivity import productivity_agent
from leo.agents.research import research_agent
from leo.config import load_config
from leo.graph.builder import build_graph
from leo.llm import gateway
from leo.memory.checkpoints import open_checkpointer
from leo.memory.memories import open_bank
from leo.memory.store import open_db
from leo.ml.embedder import load_embedder
from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.real.productivity import real_productivity_tools
from leo.tools.real.research import real_research_tools
from leo.tools.registry import by_name


# Return a schedule(seconds, label) function for start_timer: it prints a line
# when the timer is up. Timers live only while the CLI runs (saved ones: M2.7).
def timer_ringer(output_fn: Callable[[str], None], make_timer=threading.Timer):
    # Start a background timer that prints the label when it runs out.
    def schedule(seconds: float, label: str) -> None:
        timer = make_timer(seconds, lambda: output_fn(f"\n⏰ Timer '{label}' done"))
        timer.daemon = True
        timer.start()

    return schedule


# The real graph: the productivity agent with real tools on leo_data/leo.db,
# the research agent with the real web and weather tools, the calendar agent
# on the mock calendar (Radicale comes in M2.6), long-term memory, and the
# checkpointer with the rolling summary on the same database.
def default_graph(output_fn: Callable[[str], None]):
    config = load_config()
    conn = open_db(config.storage.resolved_db_path())
    tasks = by_name(real_productivity_tools(conn, schedule=timer_ringer(output_fn)))
    web = by_name(real_research_tools(config.research))
    calendar = by_name(mock_calendar_tools([]))
    steps = config.agent.max_steps
    output_fn("Note: the calendar is a mock (fixed events, nothing saved) until M2.6.")
    output_fn("Loading the embedder for memory...")
    bank = open_bank(conn, load_embedder(config.embedder), config.memory,
                     config.embedder.dimension)
    return build_graph(memory=bank, agents={
        "productivity": productivity_agent(gateway.chat, tasks, steps),
        "research": research_agent(gateway.chat, web, steps),
        "calendar": calendar_agent(gateway.chat, calendar, steps, config.calendar)},
        config=config, checkpointer=open_checkpointer(conn))
