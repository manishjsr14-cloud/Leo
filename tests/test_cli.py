"""Tests for the CLI chat loop in leo/cli.py, with a fake LLM behind the real graph."""

from langgraph.checkpoint.memory import InMemorySaver

from leo import cli, cli_setup
from leo.graph.builder import build_graph
from leo.llm.gateway import LLMUnavailable
from tests.graph_fakes import FakeChat


# Run the CLI on a fixed list of typed lines; return the printed lines.
def run_cli(lines: list[str], chat, argv: list[str] | None = None, graph=None) -> list[str]:
    typed = iter(lines)
    printed: list[str] = []

    # Like input(): the next typed line, or EOFError when there are none left.
    def fake_input(_prompt: str) -> str:
        try:
            return next(typed)
        except StopIteration:
            raise EOFError from None

    graph = graph or build_graph(chat, checkpointer=InMemorySaver())
    cli.main(argv or [], input_fn=fake_input, output_fn=printed.append, graph=graph)
    return printed


# Two turns print two replies, and the second turn sees the first one.
def test_two_turns_keep_history():
    chat = FakeChat("Hi Asha!", "Your name is Asha.")
    printed = run_cli(["my name is Asha", "what is my name?", "exit"], chat)
    assert printed[2:] == ["Leo: Hi Asha!  [ollama]", "Leo: Your name is Asha.  [ollama]"]
    second = [m["content"] for m in chat.calls[1]["messages"]]
    # The last message is the reply-language line (M1.8); the conversation is before it.
    assert second[-4:-1] == ["my name is Asha", "Hi Asha!", "what is my name?"]


# Empty lines are skipped; end of input stops the loop without an error.
def test_empty_line_skipped_and_eof_stops():
    chat = FakeChat("ok")
    printed = run_cli(["", "   ", "hello"], chat)
    assert len(chat.calls) == 1
    assert printed[-1] == "Leo: ok  [ollama]"


# --cloud sends every turn to Groq.
def test_cloud_flag_forces_every_turn():
    chat = FakeChat("one", "two")
    printed = run_cli(["hello", "again", "quit"], chat, argv=["--cloud"])
    assert [c["force_cloud"] for c in chat.calls] == [True, True]
    assert printed[-1] == "Leo: two  [groq]"


# "use cloud" sends only that turn to Groq, with the words removed.
def test_use_cloud_prefix_forces_one_turn():
    chat = FakeChat("one", "two")
    run_cli(["use cloud: what is 2+2?", "and now?", "exit"], chat)
    assert [c["force_cloud"] for c in chat.calls] == [True, False]
    assert chat.calls[0]["messages"][-2]["content"] == "what is 2+2?"


# The prefix check ignores case and leaves other messages alone.
def test_split_cloud_prefix():
    assert cli.split_cloud_prefix("Use Cloud, kal ka mausam?") == ("kal ka mausam?", True)
    assert cli.split_cloud_prefix("cloudy today?") == ("cloudy today?", False)


# A timer started by start_timer prints its label when it runs out.
def test_timer_ringer_prints_when_done():
    started = []

    # Stands in for threading.Timer: records the timer and fires it on start().
    class FakeTimer:
        def __init__(self, seconds, fn):
            self.seconds, self.fn, self.daemon = seconds, fn, False

        def start(self):
            started.append(self)
            self.fn()

    printed = []
    cli_setup.timer_ringer(printed.append, make_timer=FakeTimer)(600, "chai")
    assert started[0].seconds == 600 and started[0].daemon is True
    assert printed == ["\n⏰ Timer 'chai' done"]


# If no model can answer, the CLI says so and keeps running.
def test_llm_unavailable_keeps_loop_running():
    def failing_chat(messages, output_model=None, force_cloud=False):
        raise LLMUnavailable("Groq failed: timeout")

    printed = run_cli(["hello", "exit"], failing_chat)
    assert printed[-1].startswith("Leo: sorry, no model could answer")


# M1.8: run_turn fixes short spellings and tags the message's language.
def test_run_turn_normalizes_and_tags_the_language():
    chat = FakeChat("Theek hai.")
    _, history = cli.run_turn(build_graph(chat), [], "kl kia plan hai?", False)
    assert history[0].content == "kal kya plan hai?"
    assert "Hinglish" in chat.calls[0]["messages"][-1]["content"]
    cli.run_turn(build_graph(chat), [], "What is the plan for tomorrow?", False)
    assert "in English." in chat.calls[-1]["messages"][-1]["content"]


# M2.4: the CLI chats on the config's default thread, and says whether it is new.
def test_default_thread_and_new_line():
    chat = FakeChat("ok")
    graph = build_graph(chat, checkpointer=InMemorySaver())
    printed = run_cli(["hello"], chat, graph=graph)
    assert printed[0] == "Conversation 'laptop-cli': new."
    saved = graph.get_state({"configurable": {"thread_id": "laptop-cli"}}).values
    assert [m.content for m in saved["messages"]] == ["hello", "ok"]


# M2.4: starting the CLI again on the same thread continues the conversation.
def test_second_start_continues_the_thread():
    chat = FakeChat("Hi Asha!", "Your name is Asha.")
    graph = build_graph(chat, checkpointer=InMemorySaver())
    run_cli(["my name is Asha"], chat, graph=graph)
    printed = run_cli(["what is my name?"], chat, graph=graph)
    assert printed[0].startswith("Conversation 'laptop-cli': continuing (2 recent messages")
    second = [m["content"] for m in chat.calls[1]["messages"]]
    assert second[-4:-1] == ["my name is Asha", "Hi Asha!", "what is my name?"]


# M2.4: --thread picks another thread; --new starts a fresh one each time.
def test_thread_and_new_flags():
    chat = FakeChat("ok")
    graph = build_graph(chat, checkpointer=InMemorySaver())
    run_cli(["hello"], chat, argv=["--thread", "trip"], graph=graph)
    assert graph.get_state({"configurable": {"thread_id": "trip"}}).values["messages"]
    assert not graph.get_state({"configurable": {"thread_id": "laptop-cli"}}).values
    first = run_cli(["hi"], chat, argv=["--new"], graph=graph)[0]
    second = run_cli(["hi"], chat, argv=["--new"], graph=graph)[0]
    assert first.endswith(": new.") and second.endswith(": new.") and first != second


# M2.4: the reply is handed out as soon as the responder has it, before later nodes run.
def test_reply_shown_before_later_nodes():
    order = []

    # A node after the responder that records when it ran.
    def after(state):
        order.append("after")
        return {}

    from langgraph.graph import END, START, StateGraph

    from leo.graph.responder import responder_node
    from leo.graph.state import LeoState

    graph = StateGraph(LeoState)
    graph.add_node("responder", lambda s: responder_node(s, FakeChat("hi")))
    graph.add_node("after", after)
    graph.add_edge(START, "responder")
    graph.add_edge("responder", "after")
    graph.add_edge("after", END)
    reply, _ = cli.run_turn(graph.compile(), [], "hello", False,
                            on_reply=lambda r: order.append(r.content))
    assert order == ["hi", "after"] and reply.content == "hi"
