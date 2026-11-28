"""Tracing must never break Leo: setup, Langfuse failures and flush on exit.
No test talks to Langfuse: the clients here are fakes.
"""

import logging
from contextlib import contextmanager

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from leo import cli
from leo.config import Secrets, load_config
from leo.graph.builder import build_graph
from leo.ops import tracing
from leo.ops.langfuse_tracer import LangfuseTracer
from leo.ops.tracing_setup import setup_tracing
from tests.graph_fakes import FakeChat
from tests.tracing_fakes import FakeTracer

KEYS = {"langfuse_public_key": "pk-test", "langfuse_secret_key": "sk-test",
        "langfuse_host": "https://langfuse.invalid"}


# Secrets given here only; the real .env is not read.
def secrets(**values) -> Secrets:
    return Secrets(_env_file=None, **values)


class FakeObservation:
    """Stands in for a Langfuse observation; records updates and exits."""

    def __init__(self):
        self.updates, self.exits, self.trace_id = [], [], "t-1"

    # Record an update.
    def update(self, **fields):
        self.updates.append(fields)


class FakeLangfuse:
    """Stands in for the Langfuse client. `fail` makes every call raise."""

    def __init__(self, fail=False, auth=True):
        self.fail, self.auth, self.observations, self.flushed = fail, auth, [], 0

    # Like start_as_current_observation: a context manager giving an observation.
    def start_as_current_observation(self, **kwargs):
        if self.fail:
            raise ConnectionError("Langfuse is down: secret text 18% of 2450")
        observation = FakeObservation()
        self.observations.append(observation)

        @contextmanager
        def manager():
            yield observation
            observation.exits.append("normal")

        return manager()

    def auth_check(self):
        if self.fail:
            raise ConnectionError("down")
        return self.auth

    def flush(self):
        self.flushed += 1


# One warning-or-worse log line from Leo's tracing code.
def tracing_warnings(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records
            if r.name == "leo.ops" and r.levelno >= logging.WARNING]


def test_missing_keys_turn_tracing_off_with_one_warning(caplog):
    assert setup_tracing(load_config(), secrets()) is False
    assert isinstance(tracing.current_tracer(), tracing.NullTracer)
    reply, _ = cli.run_turn(build_graph(FakeChat("hi")), [], "hello", False)
    assert reply.content == "hi"
    assert len(tracing_warnings(caplog)) == 1


@pytest.mark.parametrize("client", [FakeLangfuse(fail=True), FakeLangfuse(auth=False)])
def test_unreachable_or_rejected_langfuse_turns_tracing_off(caplog, client):
    assert setup_tracing(load_config(), secrets(**KEYS), make_client=lambda *a: client) is False
    assert isinstance(tracing.current_tracer(), tracing.NullTracer)
    assert len(tracing_warnings(caplog)) == 1


def test_working_langfuse_is_installed():
    client = FakeLangfuse()
    assert setup_tracing(load_config(), secrets(**KEYS), make_client=lambda *a: client)
    assert isinstance(tracing.current_tracer(), LangfuseTracer)


def test_langfuse_failing_mid_session_never_breaks_requests(caplog):
    tracing.set_tracer(LangfuseTracer(FakeLangfuse(fail=True), propagate=lambda **k: None))
    graph = build_graph(FakeChat("hi"))
    for _ in range(3):
        reply, _ = cli.run_turn(graph, [], "hello", False)
        assert reply.content == "hi"
    warnings = tracing_warnings(caplog)
    assert warnings == ["tracing turned off after a Langfuse error: ConnectionError"]
    assert "18% of 2450" not in caplog.text


def test_exception_in_span_is_recorded_by_type_only():
    client = FakeLangfuse()
    tracer = LangfuseTracer(client)
    with pytest.raises(ValueError), tracer.span("tool:x", "tool", {}):
        raise ValueError("secret task title")
    (observation,) = client.observations
    assert observation.updates == [{"level": "ERROR", "status_message": "ValueError"}]
    assert observation.exits == ["normal"]  # ended without the exception's text


def test_cli_flushes_after_the_last_request():
    tracer = FakeTracer()
    tracing.set_tracer(tracer)
    lines = iter(["hello", "again"])

    # Like input(): the next line, then EOFError (the user pressed Ctrl+Z / Ctrl+D).
    def typed(_prompt: str) -> str:
        try:
            return next(lines)
        except StopIteration:
            raise EOFError from None

    graph = build_graph(FakeChat("hi"), checkpointer=InMemorySaver())
    cli.main([], input_fn=typed, output_fn=lambda _t: None, graph=graph)
    assert tracer.events.count("flush") == 1
    assert tracer.events[-1] == "flush"
    assert tracer.events.count("span:chat") == 2
