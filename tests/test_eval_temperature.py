"""Test for run_eval's --temperature override (M1 cleanup item 7, measuring only)."""

from evals import run_eval
from leo.config import load_config
from leo.llm import clients, gateway


def test_use_temperature_changes_only_what_the_gateway_sends(monkeypatch):
    monkeypatch.setattr(gateway, "load_config", gateway.load_config)   # restored after
    sent = []
    monkeypatch.setattr(clients, "run_stream", lambda client, request, timeout: sent.append(
        request) or clients.StreamResult("ok", 1, 1, 0.1, 0.2, False))
    run_eval.use_temperature(0.3)
    gateway.chat([{"role": "user", "content": "hi"}], local_client=object())
    assert sent[0]["temperature"] == 0.3
    assert gateway.load_config().llm.primary.temperature == 0.3
    assert load_config().llm.primary.temperature == 0.7              # config.yaml unchanged
