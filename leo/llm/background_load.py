"""Background model load after a first-token timeout (M2.3 fix).

In the M2.3 check every cold load of leo-qwen3 took longer than the 20 s
first-token limit; each request gave up, Ollama aborted the load, and the next
request started it again, so the model never loaded
(evals/reports/m2_3_ollama_log_notes_2026-11-26.md).

Now, when a local request hits the first-token limit, the turn still falls
back to Groq at once, and the gateway starts ONE background load request with
the long load limit (llm.primary.load_timeout_s), so the load can finish.
While it runs, other turns go straight to Groq and start no new load. When it
ends (loaded or failed), the next turn tries the local model again.
"""

import logging
import threading
from typing import Any

from leo.config import LeoConfig
from leo.llm.warmup import load_model

log = logging.getLogger("leo.llm")
_lock = threading.Lock()
_state: dict[str, Any] = {"thread": None}


# True while a background load is running.
def loading() -> bool:
    thread = _state["thread"]
    return thread is not None and thread.is_alive()


# Start the background load unless one is already running. Returns True if started.
def start_load(config: LeoConfig, client: Any = None) -> bool:
    with _lock:
        if loading():
            return False
        thread = threading.Thread(target=_load, args=(config, client), daemon=True,
                                  name="leo-model-load")
        _state["thread"] = thread
        thread.start()
    log.warning("local model still loading: started one background load")
    return True


# The background thread: load the model and log the outcome (load_model already
# turns API errors and timeouts into None).
def _load(config: LeoConfig, client: Any) -> None:
    seconds = load_model(config, client)
    outcome = "failed" if seconds is None else f"finished in {seconds:.1f} s"
    log.warning("background model load %s", outcome)


# Wait for a running background load to end (tests, shutdown). True if none is left.
def wait(timeout: float | None = None) -> bool:
    thread = _state["thread"]
    if thread is not None:
        thread.join(timeout)
    return not loading()
