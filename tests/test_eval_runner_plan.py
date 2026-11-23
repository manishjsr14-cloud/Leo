"""The eval runner records the plan as the agents that actually ran (runner fix, M1 exit check).

Runs real scenario turns through evals/run_eval.run_turn (the graph, mock tools)
with a fake LLM in place of the gateway, then scores them as the runner does.
"""

from pathlib import Path

import yaml

from evals import m1_8_check_helpers
from evals.eval_scoring import score
from leo.config import load_config
from tests.graph_fakes import FakeChat

KNOWN = yaml.safe_load(Path("evals/scenarios/m1_10_known_failing.yaml").read_text(encoding="utf-8"))


# Run one regression turn by id with these fake LLM replies; return the run and its score.
def run(turn_id: str, monkeypatch, *replies) -> tuple[dict, dict, FakeChat]:
    from evals.run_eval import run_turn

    chat = FakeChat(*replies)
    monkeypatch.setattr(m1_8_check_helpers.gateway, "chat", chat)
    turn = next(t for t in KNOWN["turns"] if t["id"] == turn_id)
    result = run_turn(turn, KNOWN, turn["lang"], load_config())
    return result, score(result), chat


# K03 is planned by the code rule (no supervisor LLM call): the plan is still ["calendar"].
def test_code_routed_turn_records_the_agents_that_ran(monkeypatch):
    result, scored, _ = run("K03", monkeypatch, {"get_events": {"range": "day"}},
                               "Saturday ko Gym aur Call hai.")
    assert result["plan"] == [["calendar"]] and scored["routing_ok"] is True
    assert not any(c["node"] == "supervisor" for c in result["calls"])


# A turn planned by the supervisor's LLM reply records the same agents as before.
def test_llm_routed_turn_records_the_same_plan(monkeypatch):
    result, scored, _ = run("K01", monkeypatch,
                            {"agents": ["productivity"], "task": "complete the milk task"},
                            {"complete_task": {"task_id": 1}})
    assert result["plan"] == [["productivity"]] and scored["routing_ok"] is True
    assert any(c["node"] == "supervisor" for c in result["calls"])
