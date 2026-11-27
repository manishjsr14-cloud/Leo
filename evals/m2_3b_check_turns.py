"""One user turn through the real graph with memory on, for the M2.3b check.

The graph is Leo's real graph (supervisor, agents on MOCK tools, responder,
memory_recall and memory_write) on the real LLM gateway and the real embedder;
the memory database is a fresh file in <temp>/leo_evals/ (evals/eval_paths.py),
never Leo's own database or leo_data/. Each turn starts a new conversation, so the only
thing carried from turn to turn is what long-term memory stored.
For each turn it records which memories the turn created and replaced (row
ids before and after), the reply, the LLM calls, the mock tools' log (each
tool call that actually ran, M2.3c) and the time taken.
"""

import time
from datetime import datetime
from pathlib import Path

import yaml

from evals.m1_5_check_helpers import tagged
from evals.m1_8_check_helpers import TimedChat
from leo import cli
from leo.agents.calendar import calendar_agent
from leo.agents.productivity import productivity_agent
from leo.agents.research import research_agent
from leo.graph.builder import build_graph
from leo.graph.memory_nodes import MemoryDecision
from leo.llm.gateway import LLMUnavailable
from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.mock.productivity import mock_productivity_tools
from leo.tools.mock.research import mock_research_tools
from leo.tools.registry import by_name

MOCK_DATA = Path("evals/scenarios/m1_8_language_turns.yaml")  # mock calendar and weather


class MemoryTimedChat(TimedChat):
    """TimedChat that labels the memory extraction call "memory"."""

    # Call the gateway; mark the call when it is the memory extraction.
    def __call__(self, messages, output_model=None, force_cloud=False):
        result = super().__call__(messages, output_model, force_cloud)
        if output_model is MemoryDecision:
            self.calls[-1]["node"] = "memory"
        return result


# The mock calendar events and weather the agents see (from the M1.8 turn file).
def mock_data() -> dict:
    data = yaml.safe_load(MOCK_DATA.read_text(encoding="utf-8"))
    return {"mock_calendar": data["mock_calendar"], "mock_weather": data["mock_weather"]}


# Leo's graph with mock tools, the given memory bank, and a fixed "now" for agents.
# Every mock tool call that runs is appended to `log` (M2.3c).
def memory_graph(bank, config, now: datetime, chat: TimedChat, data: dict, log: list):
    steps, runs = config.agent.max_steps, []
    agents = {
        "productivity": tagged(productivity_agent(chat, by_name(mock_productivity_tools(log)),
                                                  steps), "productivity", runs),
        "research": tagged(research_agent(chat, by_name(mock_research_tools(
            log, data["mock_weather"])), steps, today=lambda: now.date()), "research", runs),
        "calendar": tagged(calendar_agent(chat, by_name(mock_calendar_tools(
            log, data["mock_calendar"])), steps, config.calendar, now=lambda: now),
            "calendar", runs)}
    return build_graph(chat, agents=agents, config=config, memory=bank,
                       now=lambda: now), runs  # the responder's now (M2.3c)


# Every memory row, by id: (subject, text, active, replaced_by).
def memory_rows(bank) -> dict[int, tuple]:
    rows = bank.conn.execute("SELECT id, subject, text, active, replaced_by FROM memories")
    return {r["id"]: (r["subject"], r["text"], r["active"], r["replaced_by"]) for r in rows}


# Run one message as a new conversation. Returns what it did to memory and its reply.
def run_message(message: dict, bank, config, now: datetime, data: dict) -> dict:
    chat, log = MemoryTimedChat(), []
    graph, runs = memory_graph(bank, config, now, chat, data, log)
    before = memory_rows(bank)
    start = time.perf_counter()
    try:
        reply = str(cli.run_turn(graph, [], message["text"], False)[0].content)
    except LLMUnavailable as error:  # both models failed: report it
        reply = f"FAILED: {error!r}"
    wall = time.perf_counter() - start
    after = memory_rows(bank)
    created = sorted(set(after) - set(before))
    replaced = sorted(i for i, row in after.items()
                      if i in before and before[i][2] == 1 and row[2] == 0)
    return {"id": message["id"], "text": message["text"], "reply": reply, "turn_s": wall,
            "created": created, "replaced": replaced,
            "subjects": [after[i][0] for i in created],
            "agents": [name for name, _ in runs], "calls": chat.calls,
            "tool_log": [c.model_dump(mode="json") for c in log]}  # calls that ran (M2.3c)
