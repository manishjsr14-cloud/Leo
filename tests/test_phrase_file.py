"""The M1.6 "done when" check: >= 95 % on the frozen phrase set, which has 60+ cases.

The set is never edited to pass this test (see AGENTS.md).
"""

from pathlib import Path

from evals.m1_6_scoring import accuracy, load_set, score_set

PHRASES = Path(__file__).resolve().parent.parent / "evals/scenarios/m1_6_indian_phrases.yaml"


# The set is large enough and the parser reaches the 95 % target on it.
def test_phrase_set_accuracy():
    rows = score_set(load_set(PHRASES))
    correct, total = accuracy(rows)
    failed = [(r["id"], r["text"], r["want"], r["got"]) for r in rows if not r["ok"]]
    assert total >= 60
    assert correct / total >= 0.95, failed
