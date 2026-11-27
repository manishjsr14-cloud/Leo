"""Tests for evals/m2_3b_plans_scoring.py: which rule keeps a message out, and the
pass rule on fake records. No model is loaded; no line is from a check set."""

from datetime import datetime

import pytest

from evals.m2_3b_plans_check import result_line
from evals.m2_3b_plans_scoring import kept_out_by, parts, plan_rule

NOW = datetime(2026, 11, 27, 9, 0)


# The first rule of the write path, in the node's order.
@pytest.mark.parametrize("text, rule", [
    ("Do I have a dentist visit this evening?", "question rule"),
    ("Aaj shaam party hai.", "no first-person word"),
    ("Remind me to call my sister tonight.", "request word"),
    ("I'm fine, thanks.", "small talk"),
    ("Tonight I'm cooking dal.", "plan rule (part of today or weekend)"),
    ("Kal main Pune jaunga.", "plan rule (time parser)"),
    ("I live in Thane.", None), ("I always cook dal tonight.", None)])
def test_kept_out_by(text, rule):
    assert kept_out_by(text, NOW) == rule


# The plan rule is reported on its own even when an earlier rule keeps the message out.
def test_plan_rule_alone():
    assert plan_rule("Aaj shaam party hai.", NOW) == "plan rule (part of today or weekend)"
    assert plan_rule("I live in Thane.", NOW) is None


# Pass: no plan stored and every fact stored; a stored plan or a lost fact misses.
def test_parts():
    rule = {"plans_stored_max": 0, "facts_stored_min": 2}
    data = {"plans": [{"id": "A"}], "facts": [{"id": "B"}, {"id": "C"}]}
    good = {"A": {"created": []}, "B": {"created": [1]}, "C": {"created": [2]}}
    assert [ok for _, ok in parts(rule, data, good)] == [True, True]
    bad = {"A": {"created": [3]}, "B": {"created": [1]}, "C": {"created": []}}
    assert [ok for _, ok in parts(rule, data, bad)] == [False, False]


# The check's result line speaks of the pass rule.
def test_result_line_says_pass_rule():
    assert "pass rule met" in result_line([("a", True)])
    assert "pass rule missed" in result_line([("a", True), ("b", False)])
