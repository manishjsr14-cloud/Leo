"""Tests for evals/eval_compare.py: before/after rows, changed and newly failing turns."""

from evals import eval_compare
from evals.eval_metrics import compute


# A report dict like run_eval's .json, from (key, verdict) pairs.
def report(machine, verdicts, commit="abc", seconds=5.0):
    turns = [{"key": k, "verdict": v, "tool_fails": ["missing call x"] if v == "fail" else [],
              "reply_fails": [], "reply": "Done.", "lang": "en", "steps": [], "plan": [],
              "routing_ok": True, "tools_ok": v != "fail", "lang_ok": True, "lang_why": "",
              "known": v in ("known_failing", "fixed"), "llm_calls": 2, "turn_s": seconds,
              "refused": [], "fallback_calls": 0} for k, v in verdicts]
    records = [{"lang": "en", "routing_ok": v != "fail", "tools_ok": True, "reply_ok": True,
                "lang_ok": True, "clock_ok": True, "json_ok": True, "invented_ok": True,
                "passed": v in ("pass", "fixed"), "llm_calls": 2, "turn_s": seconds,
                "refused": [], "fallback_calls": 0} for _, v in verdicts]
    return {"machine": machine, "commit": commit, "dirty": False,
            "metrics": compute(records), "turns": turns}


# Newly failing turns and every verdict change are listed.
def test_changed_and_newly_failing(monkeypatch):
    monkeypatch.setattr(eval_compare, "code_changed", lambda a, b: False)
    before = report("Machine: desktop", [("f:a", "pass"), ("f:b", "known_failing"),
                                         ("f:c", "fail")])
    after = report("Machine: desktop", [("f:a", "fail"), ("f:b", "fixed"), ("f:c", "fail")])
    text = "\n".join(eval_compare.compare(before, after, "old", "new"))
    assert "Noise check" in text
    assert "- f:a: pass -> fail" in text
    assert "- f:b: known_failing -> fixed" in text
    assert "Newly failing turns: 1" in text
    assert "- f:a: missing call x" in text
    assert "| turn seconds |" in text


# Across machines the timing rows are left out and the reason is given.
def test_other_machine_drops_timing_rows(monkeypatch):
    monkeypatch.setattr(eval_compare, "code_changed", lambda a, b: True)
    before = report("Machine: laptop", [("f:a", "pass")], seconds=20.0)
    after = report("Machine: desktop", [("f:a", "pass")])
    text = "\n".join(eval_compare.compare(before, after, "old", "new"))
    assert "| turn seconds |" not in text
    assert "timing rows (turn seconds) are left out" in text
    assert "| routing accuracy | all | 1/1 (100.0 %) | 1/1 (100.0 %) |" in text
    assert "Code changed" in text


# A report written before scorer v2 is rescored from its replies: a turn that
# failed only v1's language check is not newly failing with v2 on both sides,
# and a language-only failure names the language reason (not "routing").
def test_rescored_with_v2_on_both_sides(monkeypatch):
    monkeypatch.setattr(eval_compare, "code_changed", lambda a, b: True)
    before = report("Machine: laptop", [("f:g", "pass")])
    after = report("Machine: laptop", [("f:g", "fail")])
    turn = after["turns"][0]
    turn.update(lang="hinglish", reply="Hi! Baat karein, kaise ho?", tools_ok=True,
                tool_fails=[], lang_ok=False, lang_why="Hindi markers: ['ho']")
    before["turns"][0].update(lang="hinglish", reply="Main theek hoon, aap batao?")
    text = "\n".join(eval_compare.compare(before, after, "old", "new"))
    assert "Newly failing turns: 1" in text
    assert "- f:g: language (v1): Hindi markers: ['ho']" in text
    assert "Newly failing turns, scorer v2 on both sides: 0" in text
    assert "| turn passed (all checks, scorer v2) | all | 1/1 (100.0 %) | 1/1 (100.0 %) |" in text


# A dirty tree means the code change cannot be told.
def test_dirty_tree_is_unknown():
    before, after = {"dirty": True, "commit": "a"}, {"dirty": False, "commit": "b"}
    assert eval_compare.code_changed(before, after) is None
