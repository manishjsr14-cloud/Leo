"""Tests for evals/eval_v2.py: the v2 language check added to eval records."""

from evals.eval_v2 import fail_reasons, with_v2


# A scored record like run_eval's, passing every check but v1's language.
def record(**changes):
    base = {"key": "f:a", "lang": "hinglish", "reply": "Hi! Baat karein, kaise ho?",
            "steps": [], "plan": [[]], "routing_ok": True, "tools_ok": None,
            "lang_ok": False, "lang_why": "Hindi markers: ['ho']", "tool_fails": [],
            "reply_fails": [], "known": False, "verdict": "fail"}
    return {**base, **changes}


def test_v2_passes_a_short_hinglish_reply_v1_failed():
    r = with_v2(record())
    assert r["lang_v2_ok"] and r["passed_v2"] and r["verdict_v2"] == "pass"
    assert r["verdict"] == "fail"                     # v1's verdict is kept as it was


def test_v2_still_fails_other_checks():
    r = with_v2(record(reply_fails=["clock_times: not in the tool results: ['7 baje']"]))
    assert not r["passed_v2"] and r["verdict_v2"] == "fail"
    r = with_v2(record(routing_ok=False))
    assert r["verdict_v2"] == "fail"


def test_v2_known_failing_turn_that_passes_is_fixed():
    assert with_v2(record(known=True))["verdict_v2"] == "fixed"


def test_tool_data_words_do_not_count_against_english():
    steps = [{"tool": "add_note", "args": {}, "result": {"text": "gas cylinder book karna hai"}}]
    r = with_v2(record(lang="en", reply="Saved 'gas cylinder book karna hai'.", steps=steps))
    assert r["lang_v2_ok"]


def test_fail_reasons_name_the_language_check():
    r = with_v2(record())
    assert fail_reasons(r, "v1") == ["language (v1): Hindi markers: ['ho']"]
    assert fail_reasons(r, "v2") == []
    r = with_v2(record(routing_ok=False, plan=[["research"]], tool_fails=["missing call x"]))
    assert fail_reasons(r, "v2") == ["plan [['research']]", "missing call x"]
