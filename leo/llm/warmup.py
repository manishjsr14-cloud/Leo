"""Warm-up: load the local model when Leo starts (M1 cleanup item 3).

The first request after Ollama has unloaded the model waits for it to load
(M1.1 model check on the laptop: first token 8.39 s cold, 2.16 s warm). So
when Leo starts, it sends one tiny request ("hi", at most 1 output token)
built like every other Ollama request (same model, think and temperature),
so the model that gets loaded is the one the chat uses. The reply is thrown
away: it is not added to the conversation, not traced and not logged as a
chat call. A failure is only logged; Leo starts anyway and the gateway's
normal fallback rules apply to the first real turn.
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


# Send the warm-up request. Returns the seconds it took, or None when the
# warm-up is off in config.yaml or the request failed.
def warm_up(config: LeoConfig | None = None, client: Any = None,
            clock: Callable[[], float] = time.monotonic) -> float | None:
    config = config or load_config()
    cfg = config.llm.primary
    if not cfg.warm_up:
        return None
    client = client or clients.ollama_client(cfg)
    start = clock()
    try:
        clients.run_stream(client, warm_up_request(config), cfg.total_timeout_s)
    except (openai.APIError, LLMTimeout) as error:
        log.warning("model warm-up failed: %s", type(error).__name__)
        return None
    return clock() - start
