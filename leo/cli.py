"""Text chat with Leo in the terminal.

  python -m leo.cli                 # local model first, Groq on fallback
  python -m leo.cli --cloud         # every turn goes to Groq
  python -m leo.cli --thread trip   # continue (or start) the conversation "trip"
  python -m leo.cli --new           # start a fresh conversation

A message starting with "use cloud" sends only that turn to Groq.
Type "exit" or "quit" (or press Ctrl+C) to stop. The conversation is saved in
leo_data/leo.db after every step (M2.4, one thread per conversation, default
conversation.thread_id), so killing the CLI and starting it again continues it.
The reply is printed as soon as the responder has it; memory_write and the
rolling summary run after that, before the next prompt.
The real graph (tools, memory, checkpoints) is built in leo/cli_setup.py.
Each message is one trace in Langfuse when the keys are set (section 13.2),
with the thread id as the session; the tracer is flushed on exit.
"""

import argparse
import logging
import uuid
from collections.abc import Callable

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage

from leo.config import load_config, load_secrets
from leo.language.normalize import language_tag, normalize
from leo.llm.gateway import LLMUnavailable
from leo.llm.warmup import warm_up
from leo.ops import tracing
from leo.ops.trace_tags import request_tags
from leo.ops.tracing_setup import setup_tracing

CLOUD_PREFIX = "use cloud"
EXIT_WORDS = {"exit", "quit"}
# Fields that belong to one request: every turn starts them empty, so a saved
# thread never hands the last turn's plan or results to the next one (M2.4).
PER_REQUEST = {"hops": 0, "plan": [], "agent_results": {}, "completed_agents": [],
               "agent_queue": [], "memories": [], "personal_question": False}


# If the message starts with "use cloud", remove those words (and a following
# ":" or ",") and return True so this turn goes to Groq.
def split_cloud_prefix(text: str) -> tuple[str, bool]:
    if not text.lower().startswith(CLOUD_PREFIX):
        return text, False
    return text[len(CLOUD_PREFIX):].lstrip(" :,-"), True


# Run one user message through the graph as one trace. Returns the reply and
# the messages in the state afterwards. With a thread_id the graph's saved
# thread supplies the earlier messages (pass history=[]); without one,
# `history` is the conversation so far. on_reply(reply) is called as soon as
# the responder has the reply, before the nodes after it run.
def run_turn(
    graph, history: list[AnyMessage], text: str, force_cloud: bool, session_id: str = "",
    thread_id: str | None = None, on_reply: Callable[[AIMessage], None] | None = None,
) -> tuple[AIMessage, list[AnyMessage]]:
    text = normalize(text)  # short spellings fixed; Devanagari left as it is (M1.8)
    state = {"messages": [*history, HumanMessage(text)], **PER_REQUEST,
             "language": language_tag(text)}
    configurable = {"force_cloud": force_cloud}
    if thread_id:
        configurable["thread_id"] = thread_id
    reply, values = None, {}
    tags, metadata = request_tags()
    with tracing.request_trace(session_id, tags, metadata):
        for mode, chunk in graph.stream(state, {"configurable": configurable},
                                        stream_mode=["updates", "values"]):
            if mode == "values":
                values = chunk
            elif "responder" in chunk:
                reply = chunk["responder"]["messages"][-1]
                if on_reply:
                    on_reply(reply)
    return reply or values["messages"][-1], values["messages"]


# Read --cloud, --thread and --new from the command line.
def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m leo.cli", description="Chat with Leo.")
    parser.add_argument("--cloud", action="store_true", help="send every turn to Groq")
    parser.add_argument("--thread", help="the conversation to continue or start")
    parser.add_argument("--new", action="store_true", help="start a fresh conversation")
    return parser.parse_args(argv)


# The thread to chat on: a fresh id with --new, else --thread, else the config default.
def pick_thread(args: argparse.Namespace) -> str:
    if args.new:
        return "cli-" + uuid.uuid4().hex[:8]
    return args.thread or load_config().conversation.thread_id


# The chat loop. input_fn, output_fn and graph can be swapped in tests (a test
# graph must have a checkpointer); with a test graph, tracing is left as the
# test set it up and there is no warm-up unless the test passes `warm`.
# With --cloud there is no warm-up.
def main(
    argv: list[str] | None = None,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    graph=None,
    warm: Callable[[], object] | None = None,
) -> None:
    args = parse_args(argv)
    if graph is None:
        from leo.cli_setup import default_graph  # loads torch; tests skip it

        setup_tracing(load_config(), load_secrets())
        graph = default_graph(output_fn)
        warm = warm or warm_up
    if warm is not None and not args.cloud:
        output_fn("Loading the local model...")
        warm()  # one tiny request, not part of the conversation (M1 cleanup)
    try:
        chat_loop(graph, args.cloud, pick_thread(args), input_fn, output_fn)
    finally:
        tracing.flush()  # send the last request's spans before exiting


# One line about the thread: new, or continued with how much it holds.
def thread_line(graph, thread_id: str) -> str:
    saved = graph.get_state({"configurable": {"thread_id": thread_id}}).values
    if not saved.get("messages"):
        return f"Conversation '{thread_id}': new."
    summary = "yes" if saved.get("summary") else "no"
    return (f"Conversation '{thread_id}': continuing ({len(saved['messages'])} recent "
            f"messages, summary: {summary}).")


# Read lines and answer them until exit, end of input or Ctrl+C.
def chat_loop(graph, cloud: bool, thread_id: str, input_fn, output_fn) -> None:
    output_fn(thread_line(graph, thread_id))
    output_fn("Leo is ready. Type 'exit' to stop." + (" (cloud mode)" if cloud else ""))

    # Print the reply as soon as the responder has it.
    def show(reply: AIMessage) -> None:
        provider = reply.response_metadata.get("provider", "?")
        output_fn(f"Leo: {reply.content}  [{provider}]")

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
            run_turn(graph, [], text, cloud or cloud_turn, thread_id, thread_id, show)
        except LLMUnavailable as error:
            output_fn(f"Leo: sorry, no model could answer ({error}).")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    main()
