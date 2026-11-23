"""Tests for the M1.10 suite and regression files: they load and fit together."""

from pathlib import Path

import yaml

SUITE = Path("evals/scenarios/m1_10_suite.yaml")
KNOWN = Path("evals/scenarios/m1_10_known_failing.yaml")


# Read a YAML file.
def load(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


# Every run file exists, has turns, and every turn gets a language.
def test_every_turn_has_a_language():
    for entry in load(SUITE)["run"]:
        data = load(entry["file"])
        for turn in data["turns"]:
            lang = turn.get("lang", entry.get("lang", {}).get(turn["id"]))
            assert lang in ("hinglish", "en"), (entry["file"], turn["id"])


# Regression cases: unique ids, known_failing with a task, a known calendar.
def test_regression_cases():
    data = load(KNOWN)
    ids = [t["id"] for t in data["turns"]]
    assert len(ids) == len(set(ids))
    for turn in data["turns"]:
        assert turn["known_failing"] is True
        assert str(turn["from"]).startswith("M1.")
        assert turn["calendar"] in data["calendars"]


# Every same_as entry names a turn that exists in a run file.
def test_same_as_points_to_real_turns():
    keys = {f"{Path(e['file']).stem}:{t['id']}"
            for e in load(SUITE)["run"] for t in load(e["file"])["turns"]}
    for turn in load(KNOWN)["turns"]:
        for key in turn.get("same_as", []):
            assert key in keys, key


# Skipped files exist and give a reason.
def test_skipped_files():
    for entry in load(SUITE)["skip"]:
        assert Path(entry["file"]).exists()
        assert entry["why"]
