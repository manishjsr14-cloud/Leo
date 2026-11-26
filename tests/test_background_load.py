"""Tests for the background model load after a first-token timeout (M2.3 fix),
with fake clients: nothing here talks to Ollama or Groq."""

import threading

from leo.config import load_config
from leo.llm import background_load, gateway
from leo.llm.clients import ollama_client
from tests import llm_fakes as fakes
from tests.llm_fakes import FakeClient

MESSAGES = [{"role": "user", "content": "hi"}]


class SlowLoadClient:
    """A model load that takes as long as the test wants: create() waits for
    `release`, then streams nothing. Records every request."""

    def __init__(self, error: Exception | None = None):
        self.requests: list[dict] = []
        self.release = threading.Event()
        self.error = error
        self.chat = self
        self.completions = self

    # Like client.chat.completions.create(**request).
    def create(self, **request):
        self.requests.append(request)
        self.release.wait(5)
        if self.error is not None:
            raise self.error
        return iter([])


# One turn through the real gateway with the given fake clients.
def turn(local, cloud, loader):
    return gateway.chat(MESSAGES, config=load_config(), local_client=local, cloud_client=cloud,
                        load_client=loader)


# A slow load completes after the first turn times out; turns meanwhile go to Groq
# without touching the local model; the next turn after it finishes is local.
def test_slow_load_finishes_and_next_turn_is_local():
    local = FakeClient(fakes.timeout_error(), "local reply")
    cloud, loader = FakeClient("groq 1", "groq 2"), SlowLoadClient()
    first = turn(local, cloud, loader)
    assert (first.provider, first.fallback_reason) == ("groq", "first_token_timeout")
    assert background_load.loading() and len(loader.requests) == 1
    assert loader.requests[0]["max_tokens"] == 1
    second = turn(local, cloud, loader)
    assert (second.provider, second.fallback_reason) == ("groq", "model_loading")
    assert len(local.requests) == 1          # the local model was not asked again
    loader.release.set()
    assert background_load.wait(5)
    third = turn(local, cloud, loader)
    assert (third.provider, third.text) == ("ollama", "local reply")
    assert len(loader.requests) == 1


# Only one load runs at a time, even when many threads ask at once.
def test_only_one_load_at_a_time():
    loader, config = SlowLoadClient(), load_config()
    results, ready = [], threading.Barrier(5)

    # Ask for a load as soon as all threads are ready.
    def ask():
        ready.wait()
        results.append(background_load.start_load(config, loader))

    threads = [threading.Thread(target=ask) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == [False, False, False, False, True]
    assert not background_load.start_load(config, loader)
    loader.release.set()
    assert background_load.wait(5) and len(loader.requests) == 1


# A failed background load ends the loading state; the next turn tries local again.
def test_failed_load_lets_the_next_turn_try_local():
    loader = SlowLoadClient(fakes.connection_error())
    loader.release.set()
    local = FakeClient(fakes.timeout_error(), "local reply")
    turn(local, FakeClient("groq"), loader)
    assert background_load.wait(5)
    assert turn(local, FakeClient("groq"), loader).provider == "ollama"


# A reply that runs past the total limit (the model was answering) starts no load.
def test_total_timeout_starts_no_load():
    config = load_config()
    config.llm.primary.total_timeout_s = 0.01
    slow = fakes.slow_stream([fakes.text_chunk("a"), fakes.text_chunk("b")], pause_s=0.05)
    loader = SlowLoadClient()
    result = gateway.chat(MESSAGES, config=config, local_client=FakeClient(slow),
                          cloud_client=FakeClient("groq"), load_client=loader)
    assert result.fallback_reason == "timeout"
    assert not background_load.loading() and loader.requests == []


# The load client has no first-token limit: its read limit is load_timeout_s.
def test_load_client_waits_for_the_load():
    cfg = load_config().llm.primary
    assert ollama_client(cfg, load=True).timeout.read == cfg.load_timeout_s
    assert ollama_client(cfg).timeout.read == cfg.first_token_timeout_s
