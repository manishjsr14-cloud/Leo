"""A fake tracer for tests: records every span in memory, sends nothing.

It tracks the current parent span in a ContextVar, the same way OpenTelemetry
(and so Langfuse) does, so a test can check that spans nest correctly even
when LangGraph runs nodes in worker threads.
"""

from contextlib import contextmanager
from contextvars import ContextVar


class FakeHandle:
    """Handle for one fake span; updates are merged into its record."""

    def __init__(self, record: dict):
        self.record = record
        self.trace_id = f"trace-{record['id']}"

    # Merge new fields into the span's record (metadata dicts are merged too).
    def update(self, **fields) -> None:
        for key, value in fields.items():
            if value is None:
                continue
            if key == "metadata" and isinstance(self.record["fields"].get("metadata"), dict):
                value = {**self.record["fields"]["metadata"], **value}
            self.record["fields"][key] = value


class FakeTracer:
    """Records spans as dicts: id, name, kind, parent id, fields, error type."""

    def __init__(self):
        self.spans: list[dict] = []
        self.events: list[str] = []  # "span:<name>" and "flush", in order
        self._current: ContextVar[int | None] = ContextVar("fake_span", default=None)

    # Record one span under the current one; note the error type if the body raises.
    @contextmanager
    def span(self, name: str, kind: str, fields: dict):
        record = {"id": len(self.spans) + 1, "name": name, "kind": kind,
                  "parent": self._current.get(), "fields": dict(fields), "error": None}
        self.spans.append(record)
        self.events.append(f"span:{name}")
        token = self._current.set(record["id"])
        try:
            yield FakeHandle(record)
        except BaseException as error:
            record["error"] = type(error).__name__
            raise
        finally:
            self._current.reset(token)

    # The root span of a request, with its trace attributes as fields.
    @contextmanager
    def request(self, name: str, session_id: str, tags: list[str], metadata: dict):
        fields = {"session_id": session_id, "tags": tags, "metadata": metadata}
        with self.span(name, "chain", fields) as root:
            yield root

    # Count the flush.
    def flush(self) -> None:
        self.events.append("flush")

    # The spans as a nested tree of (name, [children]) under `parent`.
    def tree(self, parent: int | None = None) -> list:
        return [(s["name"], self.tree(s["id"])) for s in self.spans if s["parent"] == parent]

    # The first span with this name.
    def named(self, name: str) -> dict:
        return next(s for s in self.spans if s["name"] == name)
