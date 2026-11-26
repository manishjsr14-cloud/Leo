"""Tests for the M2.3 check's scoring and report helpers, and a dry run of part A
with the fake embedding model (no real model, no LLM)."""

from pathlib import Path

from evals import m2_3_check_helpers as h
from evals.m2_3_check_parts import part_a
from tests.memory_fakes import make_bank

SET = h.load_yaml(Path(__file__).resolve().parent.parent
                  / "evals/scenarios/m2_3_memory_questions.yaml")


# Rank is 1-based; a missing text has no rank.
def test_rank_of():
    assert h.rank_of("b", ["a", "b", "c"]) == 2
    assert h.rank_of("z", ["a"]) is None


# Recall@k counts ranks at or below k; the rule needs 20 rows and >= 0.90.
def test_recall_and_rule():
    rows = [{"rank": 1}] * 17 + [{"rank": 5}] + [{"rank": None}] * 2
    assert h.recall_at(rows, 5) == 0.9 and h.recall_at(rows, 1) == 0.85
    assert h.passed(rows, SET["pass_rule"])
    assert not h.passed(rows[:-3] + [{"rank": None}] * 3, SET["pass_rule"])
    assert not h.passed(rows[:10], SET["pass_rule"])


# The M1.10 suite has 42 messages (10 + 25 + 7).
def test_suite_texts():
    from evals.m2_3_memory_check import ROOT
    assert len(h.suite_texts(ROOT / "evals" / "scenarios")) == 42


# Spread and its text form.
def test_spread_and_fmt():
    s = h.spread([3.0, 1.0, 2.0])
    assert s == {"n": 3, "median": 2.0, "min": 1.0, "max": 3.0}
    assert h.fmt(s) == "median 2.0 (min 1.0, max 3.0, n 3)"
    assert h.spread([]) is None and h.fmt(None) == "-"


FIX = h.load_yaml(Path(__file__).resolve().parent.parent
                  / "evals/scenarios/m2_3_fix_questions.yaml")


# Part A on both sets with a fake model: 33 saves, 3 replaced, 30 active, 20 + 12
# scored rows, 4 + 6 no-memory rows, a threshold, and report lines for both sets.
def test_part_a_dry_run(tmp_path):
    bank = make_bank(tmp_path)
    a, times = part_a(bank, SET, FIX)
    assert (a["saved"], a["replaced"], a["stored"]) == (33, 3, 30)
    assert [len(a["sets"][n]["questions"]) for n in ("original", "fix")] == [20, 12]
    assert [len(a["sets"][n]["no_memory"]) for n in ("original", "fix")] == [4, 6]
    assert len(times) == 32 and a["threshold_from_fix"] is not None
    lines = h.part_a_lines(a)
    assert any(line.startswith("**Recall@5 (original): ") for line in lines)
    assert any(line.startswith("**Recall@5 (fix): ") for line in lines)


# The threshold rule: the smallest two-decimal value strictly above the highest.
def test_threshold_above():
    assert h.threshold_above([0.81, 0.853, 0.84]) == 0.86
    assert h.threshold_above([0.85]) == 0.86
    assert h.threshold_above([0.799]) == 0.80
