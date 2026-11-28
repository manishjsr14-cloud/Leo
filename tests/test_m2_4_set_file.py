"""Shape checks for the frozen M2.4 restart set (no model is loaded here)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SET = ROOT / "evals/scenarios/m2_4_restart_set.yaml"


# Load the set.
def load() -> dict:
    with SET.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# 20 turns before the kill, 6 after, every id unique, asked in the agreed order.
def test_sizes_order_and_unique_ids():
    data = load()
    before = [t["id"] for t in data["before_kill"]]
    after = [t["id"] for t in data["after_restart"]]
    assert before == [f"P{n:02d}" for n in range(1, 21)]
    assert after == ["R5", "R6", "R1", "R2", "R3", "R4"]
    assert len(set(before + after)) == 26


# Every expected key appears in the line it refers back to, which is a fact line.
def test_expected_keys_come_from_earlier_lines():
    data = load()
    by_id = {t["id"]: t for t in data["before_kill"]}
    for turn in data["after_restart"]:
        source = by_id[turn["from"]]
        assert "fact" in source, turn["id"]
        assert turn["expect_any_of"][0] in source["text"], turn["id"]


# The pass rule names the recent and summarized turns as the user wrote it.
def test_pass_rule():
    data = load()
    rule = data["pass_rule"]
    assert rule["recent_answered"] == ["R5", "R6"]
    assert rule["summarized"] == ["R1", "R2", "R3", "R4"]
    assert rule["summarized_answered_min"] == 3
    where = {t["id"]: t["where"] for t in data["after_restart"]}
    assert all(where[i] == "recent" for i in rule["recent_answered"])
    assert all(where[i] == "summary" for i in rule["summarized"])
    assert data["now"] == "2026-11-28T10:00:00+05:30"
