"""Shape checks for the frozen M2.3 memory check set (no model is loaded here)."""

from pathlib import Path

import yaml

SET = Path(__file__).resolve().parent.parent / "evals/scenarios/m2_3_memory_questions.yaml"


# Load the check set once per test.
def load() -> dict:
    with SET.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# The pass rule is written into the file: part A, Recall@5 >= 0.90 on 20 questions.
def test_pass_rule_is_fixed():
    rule = load()["pass_rule"]
    assert rule == {"part": "A", "metric": "recall_at_5", "min": 0.90, "questions": 20}


# 20 scored questions, at least half Hinglish, each expecting a fact that exists
# and is still current (not replaced by a later fact).
def test_questions_point_at_current_facts():
    data = load()
    facts = {f["id"]: f for f in data["facts"]}
    replaced = {f["replaces"] for f in data["facts"] if "replaces" in f}
    questions = data["questions"]
    assert len(questions) == 20
    assert sum(q["lang"] == "hinglish" for q in questions) >= 10
    for q in questions:
        assert q["expect"] in facts and q["expect"] not in replaced, q["id"]


# Negation and g09-style questions are both present.
def test_negation_and_g09_cases_present():
    questions = load()["questions"]
    assert sum(bool(q.get("negation")) for q in questions) >= 3
    assert sum(bool(q.get("g09_style")) for q in questions) >= 2


# A replacing fact has the same subject as the fact it replaces, and comes after it;
# every other subject is used only once.
def test_replacements_share_a_subject():
    facts = load()["facts"]
    order = [f["id"] for f in facts]
    by_id = {f["id"]: f for f in facts}
    replacing = [f for f in facts if "replaces" in f]
    assert len(replacing) >= 3
    for f in replacing:
        old = by_id[f["replaces"]]
        assert old["subject"] == f["subject"]
        assert order.index(old["id"]) < order.index(f["id"])
    current = [f["subject"] for f in facts if f["id"] not in {r["replaces"] for r in replacing}]
    assert len(current) == len(set(current))


# Every fact's stored text is the user's own words, taken from the message.
def test_fact_text_is_from_the_message():
    for f in load()["facts"]:
        assert f["fact"].lower() in f["text"].lower(), f["id"]


# At least 5 plans or events must not be stored, and write_order covers every
# fact and every must-not-store message exactly once.
def test_must_not_store_and_write_order():
    data = load()
    assert len(data["must_not_store"]) >= 5
    ids = [f["id"] for f in data["facts"]] + [n["id"] for n in data["must_not_store"]]
    assert sorted(data["write_order"]) == sorted(ids)


# The no-memory questions are recorded, not scored, and expect nothing.
def test_no_memory_questions_expect_nothing():
    for q in load()["no_memory_questions"]:
        assert "expect" not in q and q["text"].strip()
