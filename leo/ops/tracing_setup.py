"""Turn tracing on at startup (Langfuse), or leave it off with one warning.

Only Langfuse's own spans are exported (should_export_span=is_langfuse_span),
so other OpenTelemetry spans in the process can never leak text. Langfuse
sends in a background thread; its own error logs are cut down to the first one.
"""

import logging
import subprocess

from leo.config import PROJECT_ROOT, LeoConfig, Secrets
from leo.ops import tracing
from leo.ops.langfuse_tracer import LangfuseTracer
from leo.ops.tracing import NullTracer, warn_once


# The current git commit (short), used as the trace's release; "unknown" if git fails.
def code_version() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=PROJECT_ROOT,
                             capture_output=True, text=True, timeout=2, check=True)
        return out.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


# Build the real Langfuse client: only Langfuse spans exported, given timeout and release.
def langfuse_client(public_key: str, secret_key: str, host: str, timeout_s: int):
    from langfuse import Langfuse, is_langfuse_span

    return Langfuse(public_key=public_key, secret_key=secret_key, base_url=host,
                    timeout=timeout_s, release=code_version(),
                    should_export_span=is_langfuse_span)


# Let only the first warning or error from Langfuse's own logger through.
def quiet_langfuse_logger() -> None:
    seen = []

    # Keep the first WARNING-or-worse record, drop later ones.
    def first_only(record: logging.LogRecord) -> bool:
        if record.levelno < logging.WARNING:
            return True
        seen.append(record)
        return len(seen) == 1

    logging.getLogger("langfuse").addFilter(first_only)


# Turn tracing on if the keys are set and Langfuse answers; otherwise leave it
# off with one warning. make_client is swapped in tests (no network).
def setup_tracing(config: LeoConfig, secrets: Secrets, make_client=langfuse_client) -> bool:
    settings = config.tracing
    tracing.set_tracer(NullTracer(), settings.include_text)
    public = secrets.langfuse_public_key.get_secret_value()
    secret = secrets.langfuse_secret_key.get_secret_value()
    if not (public and secret and secrets.langfuse_host):
        warn_once("tracing off: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY or "
                  "LANGFUSE_HOST is not set in .env")
        return False
    try:
        client = make_client(public, secret, secrets.langfuse_host, settings.timeout_s)
        reachable = client.auth_check()
    except Exception as error:  # noqa: BLE001 - tracing must never break Leo
        warn_once("tracing off: Langfuse could not be reached (%s)", type(error).__name__)
        return False
    if not reachable:
        warn_once("tracing off: Langfuse rejected the keys")
        return False
    quiet_langfuse_logger()
    tracing.set_tracer(LangfuseTracer(client), settings.include_text)
    return True
