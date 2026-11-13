"""Text chat with Leo in the terminal.

  python -m leo.cli            # local model first, Groq on fallback
  python -m leo.cli --cloud    # every turn goes to Groq

A message starting with "use cloud" sends only that turn to Groq.
Type "exit" or "quit" (or press Ctrl+C) to stop. The conversation lives in
memory only; saving it across restarts comes with checkpointing in M2.4.
"""

import argparse
import logging
from collections.abc import Callable

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage

from leo.graph.builder import build_graph
from leo.llm.gateway import LLMUnavailable

CLOUD_PREFIX = "use cloud"
EXIT_WORDS = {"exit", "quit"}


# If the message starts with "use cloud", remove those words (and a following
# ":" or ",") and return True so this turn goes to Groq.
def split_cloud_prefix(text: str) -> tuple[str, bool]:
    if not text.lower().startswith(CLOUD_PREFIX):
        return text, False
    return text[len(CLOUD_PREFIX):].lstrip(" :,-"), True


# Run one user message through the graph. Returns the reply and the new history.
def run_turn(
    graph, history: list[AnyMessage], text: str, force_cloud: bool
) -> tuple[AIMessage, list[AnyMessage]]:
    state = {"messages": [*history, HumanMessage(text)], "hops": 0, "plan": [],
             "agent_results": {}}
    out = graph.invoke(state, {"configurable": {"force_cloud": force_cloud}})
    return out["messages"][-1], out["messages"]


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
    graph = graph or build_graph()
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
