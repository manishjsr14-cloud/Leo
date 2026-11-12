"""A fake OpenAI-style client for gateway tests. No network is used.

Each call to chat.completions.create() takes the next planned outcome:
a reply string (streamed back as chunks) or an exception to raise.
"""

import time
from types import SimpleNamespace

import httpx2
import openai

REQUEST = httpx2.Request("POST", "http://fake/v1/chat/completions")


# Build one streamed chunk with some reply text and optional reasoning text.
def text_chunk(content: str, reasoning: str | None = None) -> SimpleNamespace:
    delta = SimpleNamespace(content=content, reasoning=reasoning)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)], usage=None)


# Build the last streamed chunk, which carries only the token counts.
def usage_chunk(prompt: int = 10, completion: int = 5) -> SimpleNamespace:
    usage = SimpleNamespace(prompt_tokens=prompt, completion_tokens=completion)
    return SimpleNamespace(choices=[], usage=usage)


# Stream chunks, pausing before each one (used to test the total time limit).
def slow_stream(chunks: list, pause_s: float):
    for chunk in chunks:
        time.sleep(pause_s)
        yield chunk


class FakeClient:
    """Records every request and returns planned outcomes in order."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.requests: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    # Pretend to call the API: record the request, then reply or raise.
    def _create(self, **request):
        self.requests.append(request)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        if isinstance(outcome, str):
            return iter([text_chunk(outcome), usage_chunk()])
        return outcome


# The error the SDK raises when nothing is listening (Ollama not running).
def connection_error() -> openai.APIConnectionError:
    return openai.APIConnectionError(request=REQUEST)


# The error the SDK raises when the read timeout (first token) runs out.
def timeout_error() -> openai.APITimeoutError:
    return openai.APITimeoutError(request=REQUEST)


# An HTTP error from the server, such as 404 (model not loaded) or 500 (out of memory).
def status_error(status: int, message: str) -> openai.APIStatusError:
    response = httpx2.Response(status, request=REQUEST)
    error_class = {404: openai.NotFoundError, 500: openai.InternalServerError}
    return error_class.get(status, openai.APIStatusError)(message, response=response, body=None)
