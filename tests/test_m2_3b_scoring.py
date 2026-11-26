"""Tests for the M2.3b check's scoring and report (evals/m2_3b_scoring.py, m2_3b_report.py)
with fake run records: no model, no database."""

from pathlib import Path

import yaml

from evals import m2_3b_report as report
from evals import m2_3b_scoring as s
from leo.config import load_config

SET = yaml.safe_load(Path("evals/scenarios/m2_3b_memory_set.yaml").read_text(encoding="utf-8"))
GROUPS = ("facts", "plans", "same_topic_no_cue", "updates", "boundary", "questions",
          "unanswerable")


# A fake record: rows created and replaced by one turn.
def rec(group: str, created=(), replaced=(), reply: str = "ok") -> dict:
    calls = [{"node": "memory", "provider": "ollama", "total_s": 4.0}] if created else []
    return {"group": group, "created": list(created), "replaced": list(replaced),
            "subjects": ["s"] * len(created), "agents": [], "calls": calls, "turn_s": 5.0,
            "reply": reply, "text": "t"}


# A perfect fake run: every lasting fact and boundary fact stored, plans not,
# each update replacing its fact's row. Returns (records, rows).
def perfect_run() -> tuple[dict, dict]:
    records, rows, next_row = {}, {}, 1
    for group in GROUPS:
        for m in SET[group]:
            if group in ("facts", "same_topic_no_cue", "updates", "boundary"):
                records[m["id"]] = rec(group, [next_row])
                rows[next_row] = ("s", m["text"], 1, None)
                next_row += 1
            else:
                records[m["id"]] = rec(group)
    by_message = s.rows_by_message(records)
    for u in SET["updates"]:
        old, new = by_message[u["replaces"]], by_message[u["id"]]
        records[u["id"]]["replaced"] = [old]
        rows[old] = ("s", "old", 0, new)
    return records, rows


# A perfect run meets every counted part.
def test_perfect_run_meets_every_part():
    records, rows = perfect_run()
    by_message = s.rows_by_message(records)
    questions = [s.question_result(q, True, [by_message[q["expect_any_of"][0]]], by_message)
                 for q in SET["questions"]]
    unanswerable = [{"id": x["id"], "dont_know": True} for x in SET["unanswerable"]]
    parts = s.done_parts(SET["done_rule"], SET, records, rows, questions, unanswerable)
    assert all(ok for _, ok in parts)
    assert s.other_replacements(SET, records) == {}


# Misses are counted: an unstored fact, a stored plan, an uncued replacement,
# a closed gate, and a reply without a don't-know phrase (left to the user).
def test_misses_are_counted():
    records, rows = perfect_run()
    records["F01"]["created"] = []
    records["P07"]["created"] = [99]
    records["N1"]["replaced"] = [4]
    assert s.not_stored(SET, records) == ["F01"] and s.plans_stored(SET, records) == ["P07"]
    assert s.uncued_replaced(SET, records) == ["N1"]
    assert s.other_replacements(SET, records) == {"N1": [4]}
    q = s.question_result(SET["questions"][0], False, [1], {"F01": 1})
    assert (q["hit5"], q["rank"]) == (False, 1)
    parts = s.done_parts(SET["done_rule"], SET, records, rows, [q],
                         [{"id": "X01", "dont_know": False}])
    assert [ok for _, ok in parts] == [True, False, True, False, False, None]


# A cued update that replaced another fact, or nothing, is not counted.
def test_wrong_cued_replacement_is_not_counted():
    records, rows = perfect_run()
    old = s.rows_by_message(records)["F05"]
    rows[old] = ("s", "old", 1, None)
    assert s.cued_updates(SET, records, rows)["U1"] is False


# Recall: rank of the first expected row; hit3 only within the 3 hints.
def test_question_ranks():
    q = {"id": "Q", "expect_any_of": ["A", "B"]}
    out = s.question_result(q, True, [7, 8, 9, 5, 6], {"A": 5, "B": 6})
    assert (out["rank"], out["hit5"], out["hit3"]) == (4, True, False)


# The don't-know phrases, English and Hinglish.
def test_says_dont_know():
    assert s.says_dont_know("Sorry, I don't know your mother's name.")
    assert s.says_dont_know("Mujhe nahi pata, aapne bataya nahi.")
    assert not s.says_dont_know("Your mother's name is Sunita.")


# The report renders from a fake run.
def test_report_renders():
    records, rows = perfect_run()
    questions = [s.question_result(q, True, [], {}) for q in SET["questions"]]
    unanswerable = [{"id": x["id"], "text": x["text"], "reply": "no idea", "gate": True,
                     "dont_know": False} for x in SET["unanswerable"]]
    parts = s.done_parts(SET["done_rule"], SET, records, rows, questions, unanswerable)
    run = {"machine": "Machine: test", "commit": "abc", "db": "x.db", "embedder_load_s": 1.0,
           "warm_up_s": None, "records": records, "rows": rows, "questions": questions,
           "unanswerable": unanswerable, "small_talk": [rec("small", [1]) | {"text": "I agree"}],
           "parts": parts}
    text = "\n".join(report.lines(run, SET, load_config()))
    assert "**Result: NOT MET**" in text and "I agree -> stored" in text
    assert "M1.10 suite messages (42)" in text
