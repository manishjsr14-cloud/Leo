"""LLM gateway: local model first, Groq as the fallback (architecture section 6).

Fallback triggers (section 6.1): connection error, model not found, timeouts,
out of memory or other server errors, a reply that fails the schema twice,
and the user asking for the cloud. The desktop tier exists only in config.yaml
for now; this gateway never calls it.
"""

import logging
from typing import Any

import openai
from pydantic import BaseModel, ValidationError

from leo.config import LeoConfig, load_config, load_secrets
from leo.llm import clients
from leo.llm.clients import LLMTimeout, StreamResult

log = logging.getLogger("leo.llm")


class LLMUnavailable(Exception):
    """Neither the local model nor Groq could answer."""


class LLMResult(BaseModel):
    """One answer from the gateway, with where it came from and what it cost."""

    text: str
    parsed: Any = None
    valid: bool = True
    provider: str
    model: str
    prompt_tokens: int | None
    completion_tokens: int | None
    first_token_s: float | None
    total_s: float
    thinking_seen: bool
    fallback_reason: str | None = None


# Turn a client error into a short fallback reason for the logs.
def fallback_reason(error: Exception) -> str:
    if isinstance(error, (openai.APITimeoutError, LLMTimeout)):
        return "timeout"
    if isinstance(error, openai.APIConnectionError):
        return "connection_error"
    if isinstance(error, openai.NotFoundError):
        return "model_not_found"
    text = str(error).lower()
    if "out of memory" in text or "cuda" in text:
        return "out_of_memory"
    if isinstance(error, openai.APIStatusError) and error.status_code >= 500:
        return "server_error"
    return "api_error"


# Build a result from a stream, checking it against the schema if one was given.
def _to_result(
    stream: StreamResult, provider: str, model: str, output_model: type[BaseModel] | None
) -> LLMResult:
    parsed, valid = None, True
    if output_model is not None:
        try:
            parsed = output_model.model_validate_json(stream.text)
        except ValidationError:
            valid = False
    result = LLMResult(provider=provider, model=model, valid=valid, parsed=parsed, **vars(stream))
    log.info(
        "llm call provider=%s model=%s valid=%s prompt_tokens=%s completion_tokens=%s "
        "first_token_s=%s total_s=%.2f thinking_seen=%s",
        provider, model, valid, result.prompt_tokens, result.completion_tokens,
        result.first_token_s, result.total_s, result.thinking_seen,
    )
    return result


# Try the local model up to max_bad_outputs times. Returns the last result and,
# if the gateway should fall back, the reason.
def _ask_local(config: LeoConfig, client: Any, messages: list[dict], output_model):
    cfg = config.llm.primary
    result = None
    for _ in range(cfg.max_bad_outputs):
        try:
            request = clients.ollama_request(cfg, messages, output_model)
            stream = clients.run_stream(client, request, cfg.total_timeout_s)
        except (openai.APIError, LLMTimeout) as error:
            return result, fallback_reason(error)
        result = _to_result(stream, "ollama", cfg.model, output_model)
        if result.valid:
            return result, None
    return result, "bad_output"


# Ask Groq. Raises LLMUnavailable if the key is missing, the call fails,
# or the reply fails the schema.
def _ask_groq(config: LeoConfig, client: Any, messages: list[dict], output_model) -> LLMResult:
    cfg = config.llm.fallback
    if client is None:
        key = load_secrets().groq_api_key.get_secret_value()
        if not key:
            raise LLMUnavailable("GROQ_API_KEY is not set in .env")
        client = clients.groq_client(cfg, key)
    try:
        request = clients.groq_request(cfg, messages, output_model)
        stream = clients.run_stream(client, request, cfg.timeout_s)
    except (openai.APIError, LLMTimeout) as error:
        raise LLMUnavailable(f"Groq failed: {fallback_reason(error)}") from error
    result = _to_result(stream, "groq", cfg.model, output_model)
    if not result.valid:
        raise LLMUnavailable("Groq reply did not match the schema")
    return result


# Answer a chat: local model first, Groq if a trigger fires or force_cloud is set.
# If Groq also fails, return the local result when there is one, else raise.
def chat(
    messages: list[dict],
    output_model: type[BaseModel] | None = None,
    force_cloud: bool = False,
    *,
    config: LeoConfig | None = None,
    local_client: Any = None,
    cloud_client: Any = None,
) -> LLMResult:
    config = config or load_config()
    local, reason = None, "user_override"
    if not force_cloud:
        local_client = local_client or clients.ollama_client(config.llm.primary)
        local, reason = _ask_local(config, local_client, messages, output_model)
        if reason is None:
            return local
    log.warning("falling back to groq: reason=%s", reason)
    try:
        result = _ask_groq(config, cloud_client, messages, output_model)
    except LLMUnavailable as error:
        if local is not None:
            log.warning("groq failed, returning local result: %s", error)
            return local
        raise
    result.fallback_reason = reason
    return result

