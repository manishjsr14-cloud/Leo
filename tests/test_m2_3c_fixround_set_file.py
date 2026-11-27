"""Shape checks for the frozen M2.3c fix-round set (no model is loaded here)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SET = ROOT / "evals/scenarios/m2_3c_fixround_set.yaml"
FIRST = ROOT / "evals/scenarios/m2_3c_statement_set.yaml"
SIZES = {"event_statements": 5, "first_person_statements": 4, "requests": 4}


# Load a YAML file.
def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# Every message of a set file, from its list groups.
def messages(data: dict) -> list[dict]:
    return [m for group in data.values() if isinstance(group, list) for m in group]


# Group sizes are fixed; ids and texts are new against the first M2.3c set.
def test_sizes_ids_and_texts_are_fresh():
    data, first = load(SET), messages(load(FIRST))
    for group, size in SIZES.items():
        assert len(data[group]) == size, group
    new = messages(data)
    assert len({m["id"] for m in new}) == len(new)
    assert not {m["id"] for m in new} & {m["id"] for m in first}
    assert not {m["text"] for m in new} & {m["text"] for m in first}


# Four offers and the user's "kal" line, which must get the parser's question.
def test_expectations():
    data = load(SET)
    assert [m["expect"] for m in data["event_statements"]] == ["offer"] * 4 + ["ask"]
    assert data["event_statements"][4]["text"] == "Kal Rahul ke saath call."
    assert [m["expect_write"] for m in data["requests"]] == [
        "add_task", "start_timer", "create_event", "add_task"]
    assert data["now"] == "2026-11-27T09:00:00+05:30"
