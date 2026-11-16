"""Tests for evals/m1_7_scoring.py: the M1.7 turn-file scoring rules."""

from evals.m1_7_scoring import score_turn

CREATE = {"tool": "create_event", "start": "2026-11-17T10:00:00+05:30",
          "end": "2026-11-17T11:00:00+05:30", "title_contains": "rahul"}
GOOD = {"tool": "create_event", "args": {"title": "Meeting with Rahul",
                                         "start": "2026-11-17T10:00:00+05:30",
                                         "end": "2026-11-17T11:00:00+05:30"}, "result": {}}


def test_matching_call_and_plan_pass():
    assert score_turn({"plan": ["calendar"], "calls": [CREATE]}, ["calendar"], [GOOD],
                      ["create_event"], {"calendar": "done"}) == (True, [])


def test_wrong_time_or_missing_keyword_fails():
    late = {**GOOD, "args": {**GOOD["args"], "start": "2026-11-17T11:00:00+05:30"}}
    other = {**GOOD, "args": {**GOOD["args"], "title": "Meeting"}}
    for step in (late, other):
        ok, _ = score_turn({"plan": ["calendar"], "calls": [CREATE]}, ["calendar"], [step],
                           [], {})
        assert not ok


# A refused wrong attempt before the right one still fails (strict reading).
def test_unlisted_write_attempt_fails_even_if_refused():
    wrong = {**GOOD, "args": {**GOOD["args"], "start": "2026-11-17T09:00:00+05:30"},
             "result": {"error": "use exactly start ..."}}
    ok, fails = score_turn({"plan": ["calendar"], "calls": [CREATE]}, ["calendar"],
                           [wrong, GOOD], ["create_event"], {})
    assert not ok and "unlisted write" in fails[0]


def test_cancel_must_be_refused_and_never_run():
    step = {"tool": "cancel_event", "args": {"event_id": "mock-evt-gym"},
            "result": {"error": "needs approval", "needs_approval": True}}
    expect = {"plan": ["calendar"], "calls": [{"tool": "cancel_event", "event_id": "mock-evt-gym"}],
              "refused": ["cancel_event"], "executed_none": ["cancel_event"]}
    assert score_turn(expect, ["calendar"], [step], [], {})[0]
    assert not score_turn(expect, ["calendar"], [step], ["cancel_event"], {})[0]
