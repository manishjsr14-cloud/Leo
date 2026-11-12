"""Tests for leo/llm/gateway.py with fake clients: each fallback trigger goes to Groq."""

import logging
from types import SimpleNamespace

import pytest
from pydantic import BaseModel, SecretStr

from leo.config import load_config
from leo.llm import gateway
from tests import llm_fakes as fakes
from tests.llm_fakes import FakeClient

MESSAGES = [{"role": "user", "content": "hi"}]


class Choice(BaseModel):
    """A tiny schema for bad-output tests."""

    next: str


# Ask the gateway with fake local and cloud clients.
def ask(local, cloud, output_model=None, force_cloud=False, config=None):
    return gateway.chat(
        MESSAGES, output_model, force_cloud,
        config=config or load_config(), local_client=local, cloud_client=cloud,
    )


# Errors from the local model fall back to Groq with the matching reason.
@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (fakes.connection_error(), "connection_error"),
        (fakes.status_error(404, "model 'leo-qwen3' not found"), "model_not_found"),
        (fakes.timeout_error(), "timeout"),
        (fakes.status_error(500, "CUDA error: out of memory"), "out_of_memory"),
        (fakes.status_error(500, "llama runner process has terminated"), "server_error"),
    ],
)
def test_local_errors_fall_back_to_groq(error, reason):
    cloud = FakeClient("from groq")
    result = ask(FakeClient(error), cloud)
    assert (result.provider, result.text, result.fallback_reason) == ("groq", "from groq", reason)


# A reply that runs past the total time limit falls back to Groq.
def test_total_timeout_falls_back():
    config = load_config()
    config.llm.primary.total_timeout_s = 0.01
    slow = fakes.slow_stream([fakes.text_chunk("a"), fakes.text_chunk("b")], pause_s=0.05)
    result = ask(FakeClient(slow), FakeClient("from groq"), config=config)
    assert (result.provider, result.fallback_reason) == ("groq", "timeout")


# Two replies that fail the schema fall back to Groq.
def test_bad_output_twice_falls_back():
    local = FakeClient("not json", '{"wrong": 1}')
    result = ask(local, FakeClient('{"next": "calendar"}'), output_model=Choice)
    assert len(local.requests) == 2
    assert (result.provider, result.fallback_reason) == ("groq", "bad_output")
    assert result.parsed == Choice(next="calendar")


# One bad reply followed by a good one stays local; Groq is never called.
def test_one_bad_output_then_good_stays_local():
    local, cloud = FakeClient("oops", '{"next": "research"}'), FakeClient()
    result = ask(local, cloud, output_model=Choice)
    assert result.provider == "ollama" and result.parsed == Choice(next="research")
    assert len(local.requests) == 2 and cloud.requests == []


# force_cloud skips the local model completely.
def test_force_cloud_skips_local():
    local = FakeClient()
    result = ask(local, FakeClient("from groq"), force_cloud=True)
    assert result.provider == "groq" and result.fallback_reason == "user_override"
    assert local.requests == []


# If Groq fails after a bad local reply, the local result comes back marked invalid.
def test_groq_failure_returns_local_result():
    result = ask(FakeClient("bad", "bad"), FakeClient(fakes.connection_error()),
                 output_model=Choice)
    assert result.provider == "ollama" and result.valid is False


# If Groq fails and there is no local result, a clear error is raised.
def test_groq_failure_without_local_raises():
    with pytest.raises(gateway.LLMUnavailable, match="Groq failed"):
        ask(FakeClient(fakes.connection_error()), FakeClient(fakes.connection_error()))


# A missing Groq key gives a clear error instead of a confusing API failure.
def test_missing_groq_key_raises(monkeypatch):
    monkeypatch.setattr(gateway, "load_secrets",
                        lambda: SimpleNamespace(groq_api_key=SecretStr("")))
    with pytest.raises(gateway.LLMUnavailable, match="GROQ_API_KEY"):
        ask(FakeClient(fakes.connection_error()), None)


# Each call logs tokens and latency, and the Groq key never appears in the log.
def test_logs_tokens_and_latency_without_key(monkeypatch, caplog):
    key = "gsk_fake_key_for_test"
    monkeypatch.setattr(gateway, "load_secrets",
                        lambda: SimpleNamespace(groq_api_key=SecretStr(key)))
    monkeypatch.setattr(gateway.clients, "groq_client", lambda cfg, k: FakeClient("ok"))
    with caplog.at_level(logging.INFO, logger="leo.llm"):
        ask(FakeClient(fakes.connection_error()), None)
    assert "completion_tokens=5" in caplog.text and "total_s=" in caplog.text
    assert "first_token_s=" in caplog.text and key not in caplog.text
