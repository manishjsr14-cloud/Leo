"""Tests for evals/eval_scoring.py: the M1.10 checks, refused calls and verdicts."""

from evals.eval_scoring import (
    extra_fails,
    invented_results,
    refused_calls,
    score,
    verdict,
)

REFUSED = {"tool": "cancel_event", "args": {"event_id": "mock-evt-gym"},
           "result": {"error": "needs approval", "needs_approval": True}}
GUARD = {"tool": "move_event", "args": {"event_id": "x"}, "result": {"error": "no event 'x'"}}
OK_MOVE = {"tool": "move_event", "args": {"event_id": "mock-evt-team"}, "result": {"moved": 1}}


# A run result shaped like evals/m1_8_check.run_one's, with only what score() reads.
def result(turn, plan, steps, reply="ok", tool_fails=(), reply_fails=(), lang=True):
    return {"turn": turn, "plan": [plan], "steps": steps, "reply": reply,
            "tool_fails": list(tool_fails), "reply_fails": list(reply_fails),
            "lang": (lang, "why")}


# Refused calls are listed with their reason: approval, guard error, a question.
def test_refused_calls_lists_each_reason():
    ask = {"tool": "create_event", "args": {}, "result": {"error": "x", "ask": "which kal?"}}
    found = refused_calls([REFUSED, GUARD, OK_MOVE, ask])
    assert found == ["cancel_event (needs approval)", "move_event (error: no event 'x')",
                     "create_event (user must answer)"]


# forbid_tools fails when the tool is attempted.
def test_forbid_tools():
    steps = [{"tool": "find_free_slots", "args": {}, "result": []}]
    assert extra_fails({"forbid_tools": ["find_free_slots"]}, steps)
    assert not extra_fails({"forbid_tools": ["get_events"]}, steps)


# no_refused fails on a guard refusal even when a later retry is right.
def test_no_refused():
    assert extra_fails({"no_refused": True}, [GUARD, OK_MOVE])
    assert not extra_fails({"no_refused": True}, [OK_MOVE])


# calc_numbers: the first calculate must succeed with exactly the given numbers.
def test_calc_numbers_first_attempt_only():
    good = {"tool": "calculate", "args": {"expression": "15% of 3200"},
            "result": {"result": "480"}}
    bad = {"tool": "calculate", "args": {"expression": "15% of 320 tqdm"},
           "result": {"error": "number 320 not in the message"}}
    turn = {"calc_numbers": [15, 3200]}
    assert not extra_fails(turn, [good])
    assert extra_fails(turn, [bad, good])
    assert extra_fails(turn, [])


# A success claim with no successful write is invented; negated or conditional ones are not.
def test_invented_results():
    assert invented_results("Gym cancelled.", [REFUSED])
    assert not invented_results("Gym was not cancelled; approval is needed.", [REFUSED])
    assert not invented_results("It will be cancelled once you approve.", [REFUSED])
    assert not invented_results("Meeting moved to 5 pm.", [OK_MOVE])
    assert invented_results("Trip daal diya.", [])
    assert not invented_results("Saturday ko Gym hai.", [])


# Routing and tool checks are separate; the plan failure is not a tool failure.
def test_score_separates_routing_from_tools():
    turn = {"text": "x", "expect": {"plan": ["calendar"], "calls": [{"tool": "get_events"}]}}
    record = score(result(turn, ["research"], [], tool_fails=["plan x", "missing call y"]))
    assert record["routing_ok"] is False
    assert record["tools_ok"] is False
    assert record["tool_fails"] == ["missing call y"]
    assert record["passed"] is False


# A turn with only a plan has no tool score (None) and can still pass.
def test_score_plan_only_turn():
    turn = {"text": "Hi", "expect": {"plan": []}}
    record = score(result(turn, [], []))
    assert record["tools_ok"] is None
    assert record["passed"] is True


# A reply-rule failure or a wrong language fails the reply checks.
def test_score_reply_checks():
    turn = {"text": "x", "expect": {"plan": []}}
    assert score(result(turn, [], [], reply_fails=["no_json: x"]))["json_ok"] is False
    assert score(result(turn, [], [], lang=False))["reply_ok"] is False


# Verdicts: known failing turns are never new failures; passing ones are "fixed".
def test_verdict():
    assert verdict(True, False) == "pass"
    assert verdict(False, False) == "fail"
    assert verdict(False, True) == "known_failing"
    assert verdict(True, True) == "fixed"
