"""Shape checks for the frozen M2.3b memory check set (no model is loaded here)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SET = ROOT / "evals/scenarios/m2_3b_memory_set.yaml"
SIZES = {"facts": 25, "plans": 8, "same_topic_no_cue": 3, "updates": 4, "boundary": 3,
         "questions": 15, "unanswerable": 5}


# Load the set.
def load() -> dict:
    with SET.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# Each group has its fixed size, and every id is used once.
def test_group_sizes_and_unique_ids():
    data = load()
    ids = []
    for group, size in SIZES.items():
        assert len(data[group]) == size, group
        ids += [m["id"] for m in data[group]]
        assert all(m["lang"] in ("en", "hinglish") and m["text"].strip() for m in data[group])
    assert len(ids) == len(set(ids))


# Updates and same-topic messages point at facts; questions expect stored messages
# that are still current (never a fact an update replaced).
def test_references_point_at_messages():
    data = load()
    facts = {m["id"] for m in data["facts"]}
    replaced = {u["replaces"] for u in data["updates"]}
    assert replaced <= facts and {n["topic_of"] for n in data["same_topic_no_cue"]} <= facts
    stored = facts | {m["id"] for m in data["same_topic_no_cue"] + data["updates"]}
    for q in data["questions"]:
        assert q["expect_any_of"] and set(q["expect_any_of"]) <= stored - replaced, q["id"]
    assert all("expect_any_of" not in x for x in data["unanswerable"])


# The done rule is written down with the set.
def test_done_rule():
    assert load()["done_rule"] == {
        "lasting_stored_min": 0.90, "plans_stored_max": 0, "cued_updates_replaced": 4,
        "uncued_replaced_max": 0, "recall_at_5_min": 0.90, "unanswerable_invented_max": 0,
        "boundary": "reported_only"}
