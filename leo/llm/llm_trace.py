"""Tracing for LLM calls: one "generation" span per attempt (section 13.2).

A local retry and a Groq fallback each get their own span. The span always
carries provider, model, token counts and timings; the messages and the reply
only when tracing.include_text is on.
"""

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

from leo.ops import tracing


# Open the span for one LLM attempt. Yields (span, start time).
@contextmanager
def llm_span(provider: str, model: str, messages: list[dict], output_model, attempt: int):
    started = datetime.now(UTC)
    schema = getattr(output_model, "__name__", None)
    with tracing.span(f"llm:{provider}", "generation", model=model,
                      input=tracing.text(messages),
                      metadata={"provider": provider, "attempt": attempt, "schema": schema}
                      ) as span:
        yield span, started


# Record a finished reply: tokens, time to first token, validity, and the text if allowed.
def record_result(span, started: datetime, result) -> None:
    usage = {"input": result.prompt_tokens, "output": result.completion_tokens}
    first = result.first_token_s
    span.update(
        output=tracing.text(result.text),
        usage_details={k: v for k, v in usage.items() if v is not None} or None,
        completion_start_time=None if first is None else started + timedelta(seconds=first),
        metadata={"provider": result.provider, "valid": result.valid,
                  "thinking_seen": result.thinking_seen, "first_token_s": first,
                  "total_s": round(result.total_s, 3)},
    )


# Record a failed attempt by its short reason (e.g. "timeout"), never the error text.
def record_error(span, reason: str) -> None:
    span.update(level="ERROR", status_message=reason)
