"""Shape checks for the frozen M2.3 fix-round question set (no model is loaded here)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "evals/scenarios/m2_3_fix_questions.yaml"


# Load a YAML file.
def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# About 12 questions on current facts of the original set: at least 6 Hinglish
# questions about English facts, and synonym questions including meat/non-veg.
def test_questions_point_at_current_facts():
    data = load(FIX)
    original = load(ROOT / data["facts_from"])
    facts = {f["id"]: f for f in original["facts"]}
    replaced = {f["replaces"] for f in original["facts"] if "replaces" in f}
    questions = data["questions"]
    assert len(questions) == 12
    for q in questions:
        assert q["expect"] in facts and q["expect"] not in replaced, q["id"]
    cross = [q for q in questions if q["kind"] == "cross_language"]
    assert len(cross) >= 6
    assert all(q["lang"] == "hinglish" and facts[q["expect"]]["lang"] == "en" for q in cross)
    synonyms = [q for q in questions if q["kind"] == "synonym"]
    assert any(q["expect"] == "F31" for q in synonyms)


# No question repeats a question of the original set.
def test_questions_are_fresh():
    data = load(FIX)
    original = load(ROOT / data["facts_from"])
    old = {q["text"].lower() for q in original["questions"] + original["no_memory_questions"]}
    new = data["questions"] + data["no_memory_questions"]
    assert not {q["text"].lower() for q in new} & old


# 6 no-memory questions, half Hinglish, expecting nothing; the rules are written down.
def test_no_memory_questions_and_rules():
    data = load(FIX)
    nm = data["no_memory_questions"]
    assert len(nm) == 6 and sum(q["lang"] == "hinglish" for q in nm) == 3
    assert all("expect" not in q for q in nm)
    assert data["rerun_rule"] == {"metric": "recall_at_5", "min": 0.90,
                                  "close_with_known_limits_if_below_on_both": True}
