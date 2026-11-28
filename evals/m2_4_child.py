"""One process of the M2.4 restart check: runs one part of the conversation.

  python -m evals.m2_4_child <database> <variant> <part>

variant: "summary" (the graph ends with the rolling summary, config
conversation) or "no_summary" (checkpoints only). part 1 runs P01-P20, prints
the thread's state, then waits for input like the CLI, where the parent
hard-kills it. part 2 prints the state it finds, then runs R5, R6, R1-R4.
Leo's real graph with memory OFF (the user's decision), MOCK tools, the real
LLM gateway, a fixed "now", and the checkpointer on the given temporary
database (never leo_data/). Each event is one JSON line on stdout.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

from evals.m1_5_check_helpers import tagged
from evals.m1_8_check_helpers import TimedChat
from evals.m2_3b_check_turns import mock_data
from leo import cli
from leo.agents.calendar import calendar_agent
from leo.agents.productivity import productivity_agent
from leo.agents.research import research_agent
from leo.graph.builder import build_graph
from leo.llm import gateway
from leo.llm.gateway import LLMUnavailable
from leo.llm.warmup import load_model
from leo.memory.checkpoints import open_checkpointer
from leo.memory.store import open_db
from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.mock.productivity import mock_productivity_tools
from leo.tools.mock.research import mock_research_tools
from leo.tools.registry import by_name

SET = Path("evals/scenarios/m2_4_restart_set.yaml")
THREAD = "m2.4-restart"
CONFIG = {"configurable": {"thread_id": THREAD}}


class SummaryTimedChat(TimedChat):
    """TimedChat that labels the rolling-summary call "summary"."""

    # Call the gateway; mark the call when it is the summary.
    def __call__(self, messages, output_model=None, force_cloud=False):
        result = super().__call__(messages, output_model, force_cloud)
        if str(messages[-1]["content"]).startswith("<summary>"):
            self.calls[-1]["node"] = "summary"
        return result


# Leo's graph without memory: mock tools, fixed now, checkpoints on `db`, and
# the summary for the "summary" variant. Mock tool calls go to `log`.
def restart_graph(db: Path, variant: str, config, now: datetime, chat, log: list, runs: list):
    steps, data = config.agent.max_steps, mock_data()
    agents = {
        "productivity": tagged(productivity_agent(chat, by_name(mock_productivity_tools(log)),
                                                  steps), "productivity", runs),
        "research": tagged(research_agent(chat, by_name(mock_research_tools(
            log, data["mock_weather"])), steps, today=lambda: now.date()), "research", runs),
        "calendar": tagged(calendar_agent(chat, by_name(mock_calendar_tools(
            log, data["mock_calendar"])), steps, config.calendar, now=lambda: now),
            "calendar", runs)}
    conversation = config.conversation if variant == "summary" else None
    return build_graph(chat, agents=agents, config=config, now=lambda: now,
                       checkpointer=open_checkpointer(open_db(db)), conversation=conversation)


# The thread's saved state: the summary and the messages as [type, text] pairs.
def snapshot(graph) -> dict:
    values = graph.get_state(CONFIG).values
    return {"summary": values.get("summary", ""),
            "messages": [[m.type, str(m.content)] for m in values.get("messages", [])]}


# Print one event as a JSON line.
def emit(event: dict) -> None:
    print(json.dumps(event), flush=True)


# Run one turn on the thread; returns what the report needs.
def run_one(graph, turn: dict, chat, log: list, runs: list) -> dict:
    before, first_call, first_log, first_run = snapshot(graph), len(chat.calls), len(log), len(runs)
    start, shown = time.perf_counter(), []
    try:
        reply = str(cli.run_turn(graph, [], turn["text"], False, thread_id=THREAD,
                                 on_reply=lambda r: shown.append(time.perf_counter()))[0].content)
    except LLMUnavailable as error:  # both models failed: report it
        reply = f"FAILED: {error!r}"
    end = time.perf_counter()
    after = snapshot(graph)
    return {"event": "turn", "id": turn["id"], "text": turn["text"], "reply": reply,
            "reply_s": (shown[0] - start) if shown else None, "turn_s": end - start,
            "calls": chat.calls[first_call:],
            "tool_log": [c.model_dump(mode="json") for c in log[first_log:]],
            "agents": [name for name, _ in runs[first_run:]],
            "recent_before": before["messages"], "summary_before": before["summary"],
            "messages_after": len(after["messages"]), "summary_after": after["summary"]}


# Run one part and print its events; part 1 then waits to be killed.
def main() -> None:
    db, variant, part = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    data = yaml.safe_load(SET.read_text(encoding="utf-8"))
    config, now = gateway.load_config(), datetime.fromisoformat(data["now"])
    load_model(config)  # warm-up, as the CLI does; not part of the conversation
    chat, log, runs = SummaryTimedChat(), [], []
    graph = restart_graph(db, variant, config, now, chat, log, runs)
    emit({"event": "start", "state": snapshot(graph)})
    for turn in data["before_kill" if part == "1" else "after_restart"]:
        emit(run_one(graph, turn, chat, log, runs))
    emit({"event": "state", "state": snapshot(graph)})
    if part == "1":
        emit({"event": "waiting"})
        sys.stdin.readline()  # waiting for the next message, like the CLI: killed here


if __name__ == "__main__":
    main()
