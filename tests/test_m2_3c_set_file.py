"""Shape checks for the frozen M2.3c statement set (no model is loaded here)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SET = ROOT / "evals/scenarios/m2_3c_statement_set.yaml"
T09_FILE = ROOT / "evals/scenarios/m1_7_calendar_turns.yaml"
SIZES = {"statements": 8, "questions": 4, "requests": 4, "behaviour_change": 1,
         "reported_only": 4}


# Load a YAML file.
def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# Each group has its fixed size, and every id in the set is unique.
def test_sizes_and_unique_ids():
    data = load(SET)
    for group, size in SIZES.items():
        assert len(data[group]) == size, group
    ids = [m["id"] for group in SIZES for m in data[group]]
    assert len(ids) == len(set(ids))


# Each request names the write call it must make, as the user wrote them.
def test_expected_writes():
    writes = [(m["text"], m["expect_write"]) for m in load(SET)["requests"]]
    assert writes == [("Add buy groceries to my tasks.", "add_task"),
                      ("Kal subah 9 baje dentist appointment daal do.", "create_event"),
                      ("Note kar lo: gas cylinder book karna hai.", "add_note"),
                      ("Start a 20 minute timer for tea.", "start_timer")]


# The t09 line is the M1.7 turn word for word, and the pass rule excludes it.
def test_t09_and_pass_rule():
    data = load(SET)
    t09 = next(t for t in load(T09_FILE)["turns"] if t["id"] == "t09")
    assert data["behaviour_change"][0]["text"] == t09["text"]
    assert data["pass_rule"]["m1_10_excluded"] == ["m1_7_calendar_turns:t09"]
    assert data["now"] == "2026-11-27T09:00:00+05:30"
