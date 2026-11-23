"""Tests for evals/m1_exit_check.py on small report fixtures (no model runs)."""

from pathlib import Path

import yaml

from evals.m1_exit_check import RULE_FILE, check, newly_failing

RULE = yaml.safe_load(Path(RULE_FILE).read_text(encoding="utf-8"))
LAPTOP = "Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)"
CASE = "m1_10_known_failing:K04"


# A report with these turn verdicts.
def report(verdicts: dict, machine: str = LAPTOP) -> dict:
    return {"machine": machine, "commit": "abc1234", "dirty": False,
            "turns": [{"key": k, "verdict": v} for k, v in verdicts.items()]}


BASELINE = report({CASE: "known_failing", "a:t1": "pass", "a:t2": "fail"})


# The rule file is the committed one: K04, two laptop runs, M1.10 run1 as baseline.
def test_rule_file():
    assert RULE["case"] == CASE and RULE["runs"] == 2 and RULE["machine"] == "laptop"
    assert RULE["baseline"] == "evals/reports/m1.10_eval_2026-11-23_run1.json"


# Only a turn that fails now and did not fail in the baseline is newly failing.
def test_newly_failing():
    run = report({CASE: "fixed", "a:t1": "fail", "a:t2": "fail"})
    assert newly_failing(run, BASELINE) == ["a:t1"]


# Passes only when K04 is fixed in both runs, nothing is newly failing, on the laptop.
def test_rule_verdicts():
    good = report({CASE: "fixed", "a:t1": "pass", "a:t2": "fail"})
    assert check(RULE, [("r1", good), ("r2", good)], BASELINE)[0]
    still = report({CASE: "known_failing", "a:t1": "pass", "a:t2": "fail"})
    assert not check(RULE, [("r1", good), ("r2", still)], BASELINE)[0]
    broken = report({CASE: "fixed", "a:t1": "fail", "a:t2": "fail"})
    assert not check(RULE, [("r1", good), ("r2", broken)], BASELINE)[0]
    desktop = report({CASE: "fixed"}, "Machine: desktop (GPU: NVIDIA GeForce RTX 3060)")
    assert not check(RULE, [("r1", good), ("r2", desktop)], BASELINE)[0]
    assert not check(RULE, [("r1", good)], BASELINE)[0]
