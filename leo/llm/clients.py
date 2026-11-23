"""Low-level helpers for the LLM gateway.

Builds OpenAI-compatible clients for Ollama and Groq, builds the request
settings for each, and reads a streamed reply while watching the clock.
The fallback decisions live in gateway.py.
"""

import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from openai import OpenAI, Timeout
from pydantic import BaseModel

from leo.config import FallbackLLM, PrimaryLLM

THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)


class LLMTimeout(Exception):
    """The whole reply took longer than the total time limit."""


@dataclass
class StreamResult:
    """Everything read from one streamed reply."""

    text: str
    prompt_tokens: int | None
    completion_tokens: int | None
    first_token_s: float | None
    total_s: float
    thinking_seen: bool


# Remove <think>...</think> blocks (and a stray closing tag) from a reply.
def strip_think(text: str) -> str:
    text = THINK_BLOCK.sub("", text)
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    return text.strip()


# Client for the local Ollama model. No SDK retries: a failure falls back to Groq.
# The read timeout is the first-token limit, since a stream sends nothing before it.
def ollama_client(cfg: PrimaryLLM) -> OpenAI:
    timeout = Timeout(cfg.total_timeout_s, read=cfg.first_token_timeout_s)
    return OpenAI(
        base_url=cfg.base_url.rstrip("/") + "/v1",
        api_key="ollama",  # Ollama ignores the key, but the SDK needs one
        timeout=timeout,
        max_retries=0,
    )


# Client for Groq, with the SDK's own retries for rate limits and network blips.
def groq_client(cfg: FallbackLLM, api_key: str) -> OpenAI:
    return OpenAI(
        base_url=cfg.base_url,
        api_key=api_key,
        timeout=cfg.timeout_s,
        max_retries=cfg.max_retries,
    )


# The structured-output field asking for JSON that matches a Pydantic model.
def json_schema_format(output_model: type[BaseModel]) -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": output_model.__name__,
            "schema": output_model.model_json_schema(),
        },
    }


# Settings shared by both providers: streaming, token usage, optional schema.
def _base_request(
    model: str, messages: list[dict], output_model: type[BaseModel] | None
) -> dict[str, Any]:
    request: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if output_model is not None:
        request["response_format"] = json_schema_format(output_model)
    return request


# Request settings for Ollama. "think" is sent on every call to keep thinking off,
# and the temperature from config.yaml (the Groq request sends none: provider default).
def ollama_request(
    cfg: PrimaryLLM, messages: list[dict], output_model: type[BaseModel] | None
) -> dict[str, Any]:
    request = _base_request(cfg.model, messages, output_model)
    request["temperature"] = cfg.temperature
    request["extra_body"] = {"think": cfg.think}
    return request


# Request settings for Groq, with the configured reasoning effort.
def groq_request(
    cfg: FallbackLLM, messages: list[dict], output_model: type[BaseModel] | None
) -> dict[str, Any]:
    request = _base_request(cfg.model, messages, output_model)
    request["reasoning_effort"] = cfg.reasoning_effort
    return request


# Send a request and read the streamed reply, timing the first token and the total.
# Raises LLMTimeout if the reply runs past total_timeout_s.
def run_stream(
    client: Any,
    request: dict[str, Any],
    total_timeout_s: float,
    clock: Callable[[], float] = time.monotonic,
) -> StreamResult:
    start = clock()
    parts: list[str] = []
    first_token_s = None
    prompt_tokens = completion_tokens = None
    thinking_seen = False
    for chunk in client.chat.completions.create(**request):
        if chunk.usage is not None:
            prompt_tokens = chunk.usage.prompt_tokens
            completion_tokens = chunk.usage.completion_tokens
        for choice in chunk.choices:
            content = choice.delta.content or ""
            reasoning = getattr(choice.delta, "reasoning", None) or ""
            if (content or reasoning) and first_token_s is None:
                first_token_s = clock() - start
            thinking_seen = thinking_seen or bool(reasoning)
            parts.append(content)
        if clock() - start > total_timeout_s:
            raise LLMTimeout(f"reply took longer than {total_timeout_s} s")
    raw = "".join(parts)
    return StreamResult(
        text=strip_think(raw),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        first_token_s=first_token_s,
        total_s=clock() - start,
        thinking_seen=thinking_seen or "<think>" in raw or "</think>" in raw,
    )
