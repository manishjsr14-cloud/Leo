"""Tests for the model warm-up (leo/llm/warmup.py) and its call in the CLI, with a
fake client: nothing here talks to Ollama."""

import openai
from langgraph.checkpoint.memory import InMemorySaver

from leo import cli
from leo.config import load_config
from leo.graph.builder import build_graph
from leo.llm.warmup import warm_up
from tests.graph_fakes import FakeChat


class FakeStreamClient:
    """Records each request and answers with one empty stream (no chunks)."""

    def __init__(self, error: Exception | None = None):
        self.requests, self.error = [], error
        self.chat = self
        self.completions = self

    # Like client.chat.completions.create(**request).
    def create(self, **request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return iter([])


# A config copy with warm_up set as given.
def config_with(warm: bool):
    config = load_config()
    primary = config.llm.primary.model_copy(update={"warm_up": warm})
    return config.model_copy(update={"llm": config.llm.model_copy(update={"primary": primary})})


def test_warm_up_sends_one_tiny_request_like_a_chat_request():
    config, client = config_with(True), FakeStreamClient()
    seconds = warm_up(config, client, clock=iter([1.0, 3.5]).__next__)
    assert len(client.requests) == 1
    request = client.requests[0]
    assert request["model"] == config.llm.primary.model
    assert request["max_tokens"] == 1
    assert request["extra_body"] == {"think": config.llm.primary.think}
    assert request["temperature"] == config.llm.primary.temperature
    assert request["messages"] == [{"role": "user", "content": "hi"}]
    assert seconds == 2.5


def test_warm_up_off_in_config_sends_nothing():
    client = FakeStreamClient()
    assert warm_up(config_with(False), client) is None
    assert client.requests == []


def test_failed_warm_up_does_not_raise():
    error = openai.APIConnectionError(request=None)
    client = FakeStreamClient(error)
    assert warm_up(config_with(True), client) is None
    assert len(client.requests) == 1


# Run the CLI with a fake warm-up; return (printed lines, warm-up count, chat).
def run_cli(lines: list[str], argv: list[str]):
    typed, printed, warmed = iter(lines), [], []

    # Like input(): the next typed line, or EOFError when there are none left.
    def fake_input(_prompt: str) -> str:
        try:
            return next(typed)
        except StopIteration:
            raise EOFError from None

    chat = FakeChat("Hello!")
    graph = build_graph(chat, checkpointer=InMemorySaver())
    cli.main(argv, input_fn=fake_input, output_fn=printed.append, graph=graph,
             warm=lambda: warmed.append(1))
    return printed, warmed, chat


def test_cli_warms_up_once_before_the_first_turn_and_keeps_it_out_of_history():
    printed, warmed, chat = run_cli(["hello"], [])
    assert warmed == [1]
    assert printed[0] == "Loading the local model..."
    contents = [m["content"] for m in chat.calls[0]["messages"]]
    assert contents.count("hello") == 1 and "hi" not in contents


def test_cli_in_cloud_mode_does_not_warm_up():
    printed, warmed, _ = run_cli(["hello"], ["--cloud"])
    assert warmed == []
    assert "Loading the local model..." not in printed
