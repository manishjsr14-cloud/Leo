"""Tests for leo/llm/clients.py: request settings, think stripping, stream reading."""

from pydantic import BaseModel

from leo.config import load_config
from leo.llm import clients
from tests.llm_fakes import FakeClient, text_chunk, usage_chunk

MESSAGES = [{"role": "user", "content": "hi"}]


class Choice(BaseModel):
    """A tiny schema for structured-output tests."""

    next: str


# Every request built for Ollama carries think=false (safety net, plan note test 1).
def test_ollama_request_sends_think_false():
    request = clients.ollama_request(load_config().llm.primary, MESSAGES, None)
    assert request["extra_body"]["think"] is False
    assert request["model"] == load_config().llm.primary.model


# A reply containing <think>...</think> comes back without it (plan note test 2).
def test_strip_think_removes_block():
    assert clients.strip_think("<think>\nlet me see\n</think>\n\nNew Delhi.") == "New Delhi."
    assert clients.strip_think("stray thoughts</think> New Delhi.") == "New Delhi."


# With a Pydantic model, both providers send its JSON schema in response_format.
def test_requests_carry_json_schema():
    llm = load_config().llm
    for request in (
        clients.ollama_request(llm.primary, MESSAGES, Choice),
        clients.groq_request(llm.fallback, MESSAGES, Choice),
    ):
        fmt = request["response_format"]
        assert fmt["type"] == "json_schema"
        assert fmt["json_schema"]["schema"] == Choice.model_json_schema()


# Without a model, no response_format is sent.
def test_plain_request_has_no_schema():
    request = clients.ollama_request(load_config().llm.primary, MESSAGES, None)
    assert "response_format" not in request


# Groq gets the configured reasoning effort and never the Ollama-only think field.
def test_groq_request_uses_reasoning_effort():
    request = clients.groq_request(load_config().llm.fallback, MESSAGES, None)
    assert request["reasoning_effort"] == "low"
    assert "extra_body" not in request
    assert "temperature" not in request


# Every Ollama request carries the temperature from config.yaml (0.7, M1 exit check).
def test_ollama_request_sends_config_temperature():
    request = clients.ollama_request(load_config().llm.primary, MESSAGES, None)
    assert request["temperature"] == 0.7


# Reading a stream joins the text, keeps token counts and notices reasoning text.
def test_run_stream_collects_text_tokens_and_reasoning():
    chunks = [text_chunk("", reasoning="hmm"), text_chunk("New "), text_chunk("Delhi."),
              usage_chunk(prompt=12, completion=7)]
    result = clients.run_stream(FakeClient(iter(chunks)), {}, total_timeout_s=60)
    assert result.text == "New Delhi."
    assert (result.prompt_tokens, result.completion_tokens) == (12, 7)
    assert result.thinking_seen is True
    assert result.first_token_s is not None


# A plain reply with no reasoning and no think tags is marked as not thinking.
def test_run_stream_without_thinking():
    result = clients.run_stream(FakeClient("New Delhi."), {}, total_timeout_s=60)
    assert result.thinking_seen is False


# <think> tags in the reply text count as thinking, and are stripped.
def test_run_stream_detects_think_tags():
    result = clients.run_stream(FakeClient("<think>x</think>Hi"), {}, total_timeout_s=60)
    assert result.thinking_seen is True
    assert result.text == "Hi"
