"""Shape checks for the frozen M2.3b plan-rule follow-up set (no model is loaded here)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SET = ROOT / "evals/scenarios/m2_3b_plans_set.yaml"
EARLIER = [ROOT / "evals/scenarios/m2_3b_memory_set.yaml",
           ROOT / "evals/scenarios/m2_3b_fixround_set.yaml"]
SIZES = {"plans": 8, "facts": 6, "reported_only": 1}


# Load a YAML file.
def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# Every message of a set file, from its list groups.
def messages(data: dict) -> list[dict]:
    return [m for group in data.values() if isinstance(group, list) for m in group]


# Each group has its fixed size; new ids are unique and unused by the earlier sets.
def test_sizes_and_fresh_ids():
    data = load(SET)
    for group, size in SIZES.items():
        assert len(data[group]) == size, group
    new = [m["id"] for g in ("plans", "facts") for m in data[g]]
    old = {m["id"] for path in EARLIER for m in messages(load(path))}
    assert len(new) == len(set(new)) and not set(new) & old


# New texts are new; the reported-only line is fix-round P10, word for word.
def test_texts():
    data = load(SET)
    old = {m["id"]: m["text"] for path in EARLIER for m in messages(load(path))}
    new = {m["text"].lower() for g in ("plans", "facts") for m in data[g]}
    assert not new & {t.lower() for t in old.values()}
    assert [(m["id"], m["text"]) for m in data["reported_only"]] == [("P10", old["P10"])]


# The pass rule is written down with the set.
def test_pass_rule():
    assert load(SET)["pass_rule"] == {"plans_stored_max": 0, "facts_stored_min": 6,
                                      "reported_only": ["P10"]}
