"""Shape checks for the frozen M2.3b fix-round set (no model is loaded here)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SET = ROOT / "evals/scenarios/m2_3b_fixround_set.yaml"
SIZES = {"plans": 3, "small_talk": 6, "same_topic_no_cue": 2, "updates": 3,
         "reported_only": 1, "questions": 12, "unanswerable": 3}
STORED = ("facts", "same_topic_no_cue", "updates", "boundary")


# Load a YAML file.
def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# Each group has its fixed size; ids are new and unique across both sets.
def test_sizes_and_fresh_ids():
    data, first = load(SET), load(ROOT / load(SET)["runs_after"])
    old = {m["id"] for group in first.values() if isinstance(group, list) for m in group}
    ids = [m["id"] for g, size in SIZES.items() for m in data[g]]
    for group, size in SIZES.items():
        assert len(data[group]) == size, group
    assert len(ids) == len(set(ids)) and not set(ids) & old


# Updates and additions point at facts of the first set; questions expect
# memories that are current after every update of both sets.
def test_references():
    data, first = load(SET), load(ROOT / load(SET)["runs_after"])
    facts = {m["id"] for m in first["facts"]}
    assert {u["replaces"] for u in data["updates"]} <= facts
    assert {n["topic_of"] for n in data["same_topic_no_cue"]} <= facts
    stored = {m["id"] for g in STORED for m in first[g]}
    stored |= {m["id"] for g in ("same_topic_no_cue", "updates") for m in data[g]}
    replaced = {u["replaces"] for u in first["updates"] + data["updates"]}
    for q in data["questions"]:
        assert set(q["expect_any_of"]) <= stored - replaced, q["id"]
    texts = {m["text"].lower() for g in first.values() if isinstance(g, list) for m in g}
    assert not {m["text"].lower() for g in SIZES for m in data[g]} & texts


# The pass rule is written down with the set.
def test_pass_rule():
    assert load(SET)["pass_rule"] == {
        "cued_updates_replaced": 3, "uncued_replaced_max": 0, "plans_stored_max": 0,
        "small_talk_stored_max": 0, "recall_at_5_min": 0.90, "unanswerable_invented_max": 0,
        "reported_only": ["R1"]}
