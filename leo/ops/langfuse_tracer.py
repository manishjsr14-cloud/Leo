"""The Langfuse tracer behind leo/ops/tracing.py (Langfuse SDK 5, OpenTelemetry).

Spans are made by hand with start_as_current_observation; no automatic
integration is used (see tracing.py). Only Langfuse's own spans are exported
(should_export_span=is_langfuse_span), so other OpenTelemetry spans in the
process can never leak text.

Never breaks a request: every Langfuse call is wrapped. The first failure logs
one warning and turns tracing off for the rest of the process. Langfuse sends
in a background thread. Setup lives in leo/ops/tracing_setup.py.
"""

from contextlib import contextmanager

from leo.ops import tracing
from leo.ops.tracing import NULL_HANDLE, warn_once


class SafeHandle:
    """A Langfuse observation whose updates can never raise."""

    def __init__(self, observation, tracer: "LangfuseTracer"):
        self.observation, self.tracer = observation, tracer
        self.trace_id = getattr(observation, "trace_id", None)

    # Update the observation; on any error turn tracing off.
    def update(self, **fields) -> None:
        if self.tracer.broken:
            return
        try:
            self.observation.update(**tracing.clean(fields))
        except Exception as error:  # noqa: BLE001 - tracing must never break Leo
            self.tracer.fail(error)


class LangfuseTracer:
    """Sends spans to Langfuse until the first error, then does nothing."""

    def __init__(self, client, propagate=None):
        self.client, self.propagate, self.broken = client, propagate, False

    # Turn tracing off after an error, with one warning (the error's type only).
    def fail(self, error: Exception) -> None:
        self.broken = True
        warn_once("tracing turned off after a Langfuse error: %s", type(error).__name__)

    # One observation. An exception from the code inside is recorded only by its
    # type name (its message may hold user text), then raised as usual.
    @contextmanager
    def span(self, name: str, kind: str, fields: dict):
        manager = observation = None
        if not self.broken:
            try:
                manager = self.client.start_as_current_observation(
                    name=name, as_type=kind, **fields)
                observation = manager.__enter__()
            except Exception as error:  # noqa: BLE001 - tracing must never break Leo
                self.fail(error)
        if observation is None:
            yield NULL_HANDLE
            return
        failed = None
        try:
            yield SafeHandle(observation, self)
        except BaseException as error:
            failed = error
            raise
        finally:
            try:
                if failed is not None:
                    observation.update(level="ERROR", status_message=type(failed).__name__)
                manager.__exit__(None, None, None)  # never pass the exception text on
            except Exception as error:  # noqa: BLE001 - tracing must never break Leo
                self.fail(error)

    # The root span of a request, with session id, tags and metadata on every span.
    @contextmanager
    def request(self, name: str, session_id: str, tags: list[str], metadata: dict):
        with self.span(name, "chain", {}) as root:
            attributes = None
            if root is not NULL_HANDLE:
                try:
                    propagate = self.propagate or _propagate_attributes()
                    attributes = propagate(session_id=session_id, trace_name=name,
                                           tags=tags, metadata=metadata)
                    attributes.__enter__()
                except Exception as error:  # noqa: BLE001 - tracing must never break Leo
                    self.fail(error)
                    attributes = None
            try:
                yield root
            finally:
                if attributes is not None:
                    try:
                        attributes.__exit__(None, None, None)
                    except Exception as error:  # noqa: BLE001 - tracing must never break Leo
                        self.fail(error)

    # Send everything still queued.
    def flush(self) -> None:
        if not self.broken:
            self.client.flush()


# Langfuse's propagate_attributes, imported only when tracing is really on.
def _propagate_attributes():
    from langfuse import propagate_attributes

    return propagate_attributes
