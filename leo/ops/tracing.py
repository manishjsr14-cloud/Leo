"""Tracing for Leo (architecture section 13.2): one trace per request, with spans
for graph nodes, agent steps, LLM calls and tool calls.

Leo's code calls only the functions here: span(), request_trace(), text(),
flush(). Which tracer is behind them is set once at startup
(leo/ops/langfuse_tracer.py) or by tests (a fake tracer). The default does
nothing, so importing Leo or running tests never sends anything anywhere.

Spans are created by hand only. Langfuse's automatic integrations (OpenAI
wrapper, LangChain/LangGraph callback handler) are never used, because they
record full prompts and replies whatever include_text says.

include_text (config tracing.include_text, default false): when false, text()
returns None, so message text, prompts, tool arguments, tool results and
replies never reach a span. Error messages count as text: only the error's
type name is recorded.
"""

import logging
from contextlib import contextmanager
from typing import Any

log = logging.getLogger("leo.ops")


class NullHandle:
    """The span handle when tracing is off: updates are ignored."""

    trace_id = None

    # Ignore the update.
    def update(self, **fields: Any) -> None:
        pass


NULL_HANDLE = NullHandle()


class NullTracer:
    """Tracing off: every call does nothing."""

    # A span that records nothing.
    @contextmanager
    def span(self, name: str, kind: str, fields: dict):
        yield NULL_HANDLE

    # A request trace that records nothing.
    @contextmanager
    def request(self, name: str, session_id: str, tags: list[str], metadata: dict):
        yield NULL_HANDLE

    # Nothing to send.
    def flush(self) -> None:
        pass


# The active tracer and settings. Set at startup or by tests, read by everyone.
_state: dict[str, Any] = {"tracer": NullTracer(), "include_text": False,
                          "warned": False, "last_trace_id": None}


# Install a tracer (Langfuse, fake or null) and the include_text setting.
def set_tracer(tracer, include_text: bool = False) -> None:
    _state["tracer"] = tracer
    _state["include_text"] = include_text


# The tracer now in use.
def current_tracer():
    return _state["tracer"]


# Log a tracing warning only once per process, so a dead Langfuse is one line, not hundreds.
def warn_once(message: str, *args: Any) -> None:
    if not _state["warned"]:
        _state["warned"] = True
        log.warning(message, *args)


# Allow warn_once to warn again (used by tests).
def reset_warning() -> None:
    _state["warned"] = False


# Pass `value` through only when include_text is on; otherwise None (left out of spans).
def text(value: Any) -> Any:
    return value if _state["include_text"] else None


# Drop None values (and None values inside a metadata dict) before they reach a span.
def clean(fields: dict) -> dict:
    out = {k: v for k, v in fields.items() if v is not None}
    if isinstance(out.get("metadata"), dict):
        out["metadata"] = {k: v for k, v in out["metadata"].items() if v is not None}
    return out


# Open a span under the current one. kind: "span", "chain", "agent", "tool"
# or "generation". Yields a handle with update(**fields).
@contextmanager
def span(name: str, kind: str = "span", **fields: Any):
    with _state["tracer"].span(name, kind, clean(fields)) as handle:
        yield handle


# Open the root span of one request; every span inside belongs to this trace.
@contextmanager
def request_trace(session_id: str, tags: list[str], metadata: dict):
    with _state["tracer"].request("chat", session_id, tags, clean(metadata)) as root:
        _state["last_trace_id"] = root.trace_id
        yield root


# The id of the most recent request's trace (None when tracing is off).
def last_trace_id() -> str | None:
    return _state["last_trace_id"]


# Send any spans still waiting. Never raises.
def flush() -> None:
    try:
        _state["tracer"].flush()
    except Exception as error:  # noqa: BLE001 - tracing must never break Leo
        warn_once("tracing flush failed: %s", type(error).__name__)

