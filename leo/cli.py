"""Text chat with Leo in the terminal.

  python -m leo.cli            # local model first, Groq on fallback
  python -m leo.cli --cloud    # every turn goes to Groq

A message starting with "use cloud" sends only that turn to Groq.
Type "exit" or "quit" (or press Ctrl+C) to stop. The conversation lives in
memory only; saving it across restarts comes with checkpointing in M2.4.
The productivity agent keeps tasks and notes in leo_data/leo.db.
"""

import argparse
import logging
import threading
from collections.abc import Callable

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage

from leo.agents.productivity import productivity_agent
from leo.config import load_config
from leo.graph.builder import build_graph
from leo.llm import gateway
from leo.llm.gateway import LLMUnavailable
from leo.memory.store import open_db
from leo.tools.real.productivity import real_productivity_tools
from leo.tools.registry import by_name

CLOUD_PREFIX = "use cloud"
EXIT_WORDS = {"exit", "quit"}


# If the message starts with "use cloud", remove those words (and a following
# ":" or ",") and return True so this turn goes to Groq.
def split_cloud_prefix(text: str) -> tuple[str, bool]:
    if not text.lower().startswith(CLOUD_PREFIX):
        return text, False
    return text[len(CLOUD_PREFIX):].lstrip(" :,-"), True


# Run one user message through the graph. Returns the reply and the new history.
# Per-request fields (hops, plan, agent results, completed agents) start empty.
def run_turn(
    graph, history: list[AnyMessage], text: str, force_cloud: bool
) -> tuple[AIMessage, list[AnyMessage]]:
    state = {"messages": [*history, HumanMessage(text)], "hops": 0, "plan": [],
             "agent_results": {}, "completed_agents": []}
    out = graph.invoke(state, {"configurable": {"force_cloud": force_cloud}})
    return out["messages"][-1], out["messages"]


# Return a schedule(seconds, label) function for start_timer: it prints a line
# when the timer is up. Timers live only while the CLI runs (saved ones: M2.7).
def timer_ringer(output_fn: Callable[[str], None], make_timer=threading.Timer):
    # Start a background timer that prints the label when it runs out.
    def schedule(seconds: float, label: str) -> None:
        timer = make_timer(seconds, lambda: output_fn(f"\n⏰ Timer '{label}' done"))
        timer.daemon = True
        timer.start()

    return schedule


# The real graph: the productivity agent with real tools on leo_data/leo.db.
def default_graph(output_fn: Callable[[str], None]):
    config = load_config()
    conn = open_db(config.storage.resolved_db_path())
    tools = by_name(real_productivity_tools(conn, schedule=timer_ringer(output_fn)))
    agent = productivity_agent(gateway.chat, tools, config.agent.max_steps)
    return build_graph(agents={"productivity": agent}, config=config)


# Read --cloud from the command line.
def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m leo.cli", description="Chat with Leo.")
    parser.add_argument("--cloud", action="store_true", help="send every turn to Groq")
    return parser.parse_args(argv)


# The chat loop. input_fn, output_fn and graph can be swapped in tests.
def main(
    argv: list[str] | None = None,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    graph=None,
) -> None:
    args = parse_args(argv)
    graph = graph or default_graph(output_fn)
    history: list[AnyMessage] = []
    output_fn("Leo is ready. Type 'exit' to stop." + (" (cloud mode)" if args.cloud else ""))
    while True:
        try:
            line = input_fn("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if line.lower() in EXIT_WORDS:
            break
        text, cloud_turn = split_cloud_prefix(line)
        if not text:
            continue
        try:
            reply, history = run_turn(graph, history, text, args.cloud or cloud_turn)
        except LLMUnavailable as error:
            output_fn(f"Leo: sorry, no model could answer ({error}).")
            continue
        provider = reply.response_metadata.get("provider", "?")
        output_fn(f"Leo: {reply.content}  [{provider}]")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    main()
