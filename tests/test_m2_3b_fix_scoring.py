"""Tests for the M2.3b fix-round scoring and report (evals/m2_3b_scoring.fix_parts,
evals/m2_3b_report_fix.py) with fake records: no model, no database."""

from pathlib import Path

import yaml

from evals import m2_3b_report_fix as report_fix
from evals import m2_3b_scoring as s
from leo.config import load_config
from tests.test_m2_3b_scoring import perfect_run, rec

FIX = yaml.safe_load(Path("evals/scenarios/m2_3b_fixround_set.yaml").read_text(encoding="utf-8"))
GROUPS = ("plans", "small_talk", "same_topic_no_cue", "updates", "reported_only", "questions",
          "unanswerable")


# The first set's perfect run, then a perfect fix round: additions and updates
# stored, each update replacing its first-set fact; nothing else stored.
def perfect_fix_run() -> tuple[dict, dict, dict]:
    records, rows = perfect_run()
    fix_records, next_row = {}, max(rows) + 1
    for group in GROUPS:
        for m in FIX[group]:
            stored = group in ("same_topic_no_cue", "updates")
            fix_records[m["id"]] = rec("fix_" + group, [next_row] if stored else [])
            if stored:
                rows[next_row] = ("s", m["text"], 1, None)
                next_row += 1
    by_message = s.rows_by_message({**records, **fix_records})
    for u in FIX["updates"]:
        old, new = by_message[u["replaces"]], by_message[u["id"]]
        fix_records[u["id"]]["replaced"] = [old]
        rows[old] = ("s", "old", 0, new)
    return {**records, **fix_records}, fix_records, rows


# A perfect fix round meets every part.
def test_perfect_fix_round_meets_every_part():
    every, _, rows = perfect_fix_run()
    by_message = s.rows_by_message(every)
    questions = [s.question_result(q, True, [by_message[q["expect_any_of"][0]]], by_message)
                 for q in FIX["questions"]]
    parts = s.fix_parts(FIX["pass_rule"], FIX, every, rows, questions,
                        [{"id": x["id"], "dont_know": True} for x in FIX["unanswerable"]])
    assert all(ok for _, ok in parts)


# Stored small talk and plans, and a missing update, are counted as misses.
def test_fix_round_misses():
    every, _, rows = perfect_fix_run()
    every["S05"]["created"], every["P10"]["created"] = [500], [501]
    old = s.rows_by_message(every)["F23"]
    rows[old] = ("s", "old", 1, None)
    q = [s.question_result(FIX["questions"][0], True, [], {})]
    parts = s.fix_parts(FIX["pass_rule"], FIX, every, rows, q, [])[:4]
    assert [ok for _, ok in parts] == [False, True, False, False]


# The fix-round report renders and says S01-S06 are not blind.
def test_fix_report_renders():
    every, fix_records, rows = perfect_fix_run()
    questions = [s.question_result(q, False, [], {}) for q in FIX["questions"]]
    unanswerable = [{"id": x["id"], "text": x["text"], "reply": "?", "gate": True,
                     "dont_know": False} for x in FIX["unanswerable"]]
    run = {"machine": "Machine: test", "commit": "abc", "db": "x.db", "rows": rows,
           "embedder_load_s": 1.0, "warm_up_s": 2.0, "records": fix_records,
           "questions": questions, "unanswerable": unanswerable,
           "parts": s.fix_parts(FIX["pass_rule"], FIX, every, rows, questions, unanswerable)}
    text = "\n".join(report_fix.lines(run, FIX, load_config()))
    assert "**Result: NOT MET**" in text and "Not blind" in text and "R1 (" in text
