"""Warm-up: load the local model when Leo starts (M1 cleanup item 3).

The first request after Ollama has unloaded the model waits for it to load
(M1.1 model check on the laptop: first token 8.39 s cold, 2.16 s warm). So
when Leo starts, it sends one tiny request ("hi", at most 1 output token)
built like every other Ollama request (same model, think and temperature),
so the model that gets loaded is the one the chat uses. The reply is thrown
away: it is not added to the conversation, not traced and not logged as a
chat call. A failure is only logged; Leo starts anyway and the gateway's
normal fallback rules apply to the first real turn.

M2.3 fix: the warm-up (and the gateway's background load) waits for the load
with no first-token limit, up to llm.primary.load_timeout_s. With the 20 s
first-token limit, every cold load in the M2.3 check was aborted by Ollama
when the client gave up (evals/reports/m2_3_ollama_log_notes_2026-11-26.md).
"""

import logging
import time
from collections.abc import Callable
from typing import Any

import openai

from leo.config import LeoConfig, load_config
from leo.llm import clients
from leo.llm.clients import LLMTimeout

log = logging.getLogger("leo.llm")
WARM_UP_MESSAGES = [{"role": "user", "content": "hi"}]


# The warm-up request: an ordinary Ollama request asking for one token.
def warm_up_request(config: LeoConfig) -> dict[str, Any]:
    request = clients.ollama_request(config.llm.primary, WARM_UP_MESSAGES, None)
    request["max_tokens"] = 1
    return request


# Load the local model with one tiny request, waiting up to load_timeout_s with
# no first-token limit. Returns the seconds it took, or None if it failed.
def load_model(config: LeoConfig, client: Any = None,
               clock: Callable[[], float] = time.monotonic) -> float | None:
    cfg = config.llm.primary
    client = client or clients.ollama_client(cfg, load=True)
    start = clock()
    try:
        clients.run_stream(client, warm_up_request(config), cfg.load_timeout_s)
    except (openai.APIError, LLMTimeout) as error:
        log.warning("model load failed: %s", type(error).__name__)
        return None
    return clock() - start


# The warm-up at startup: load the model, unless the warm-up is off in config.yaml
# (then None). Returns the seconds it took, or None if it failed.
def warm_up(config: LeoConfig | None = None, client: Any = None,
            clock: Callable[[], float] = time.monotonic) -> float | None:
    config = config or load_config()
    if not config.llm.primary.warm_up:
        return None
    return load_model(config, client, clock)
