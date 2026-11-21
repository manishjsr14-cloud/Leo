"""Tests for the CLI chat loop in leo/cli.py, with a fake LLM behind the real graph."""

from leo import cli
from leo.graph.builder import build_graph
from leo.llm.gateway import LLMUnavailable
from tests.graph_fakes import FakeChat


# Run the CLI on a fixed list of typed lines; return the printed lines.
def run_cli(lines: list[str], chat, argv: list[str] | None = None) -> list[str]:
    typed = iter(lines)
    printed: list[str] = []

    # Like input(): the next typed line, or EOFError when there are none left.
    def fake_input(_prompt: str) -> str:
        try:
            return next(typed)
        except StopIteration:
            raise EOFError from None

    cli.main(argv or [], input_fn=fake_input, output_fn=printed.append,
             graph=build_graph(chat))
    return printed


# Two turns print two replies, and the second turn sees the first one.
def test_two_turns_keep_history():
    chat = FakeChat("Hi Asha!", "Your name is Asha.")
    printed = run_cli(["my name is Asha", "what is my name?", "exit"], chat)
    assert printed[1:] == ["Leo: Hi Asha!  [ollama]", "Leo: Your name is Asha.  [ollama]"]
    second = [m["content"] for m in chat.calls[1]["messages"]]
    assert second[-3:] == ["my name is Asha", "Hi Asha!", "what is my name?"]


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
    assert chat.calls[0]["messages"][-1]["content"] == "what is 2+2?"


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
    cli.timer_ringer(printed.append, make_timer=FakeTimer)(600, "chai")
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
    assert "Hinglish" in chat.calls[0]["messages"][0]["content"]
    cli.run_turn(build_graph(chat), [], "What is the plan for tomorrow?", False)
    assert "in English." in chat.calls[-1]["messages"][0]["content"]
