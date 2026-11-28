"""Tests for the M2.4 restart check's scoring (evals/m2_4_scoring.py), on hand-made results."""

from evals import m2_4_scoring as sc

RULE = {"recent_answered": ["R5", "R6"], "summarized": ["R1", "R2", "R3", "R4"],
        "summarized_answered_min": 3}
STATE = {"summary": "- train 12956", "messages": [["human", "hi"], ["ai", "hello"]]}


# One after-restart turn with this reply and these keys.
def turn(reply: str, keys: list[str]) -> dict:
    return {"reply": reply, "keys": keys}


# Answered: any key, case does not matter.
def test_answered():
    assert sc.answered("Coach b3, seats 41 and 42.", ["B3"])
    assert sc.answered("Dedh baje.", ["1:30", "dedh"])
    assert not sc.answered("I don't know.", ["B3"])


# Every part met; then 2 of R1-R4 misses the second part only.
def test_pass_parts():
    turns = {"R5": turn("B3", ["B3"]), "R6": turn("1:30 pm", ["1:30"]),
             "R1": turn("12956", ["12956"]), "R2": turn("HX4471", ["HX4471"]),
             "R3": turn("Govind", ["Govind"]), "R4": turn("not sure", ["25000"])}
    assert [ok for _, ok in sc.pass_parts(RULE, turns, STATE, STATE)] == [True, True, True]
    turns["R3"] = turn("no idea", ["Govind"])
    parts = sc.pass_parts(RULE, turns, STATE, STATE)
    assert [ok for _, ok in parts] == [True, False, True]
    assert "2 of 4" in parts[1][0]


# The state check needs a summary and the same messages.
def test_state_kept():
    assert sc.state_kept(STATE, STATE)
    assert not sc.state_kept(STATE, {**STATE, "summary": ""})
    assert not sc.state_kept(STATE, {**STATE, "messages": [["human", "hi"]]})


# Where the fact was: a recent message, the summary, or neither.
def test_where_found():
    t = {"recent_before": [["human", "Our seats are 41 and 42 in coach B3."]],
         "summary_before": "- hotel booking HX4471"}
    assert sc.where_found(t, "Our seats are 41 and 42 in coach B3.", ["B3"]) == "recent"
    assert sc.where_found(t, "Hotel ka booking ID HX4471 hai.", ["HX4471"]) == "summary"
    assert sc.where_found(t, "The cab driver's name is Govind.", ["Govind"]) == "neither"


# Token figures per turn and in total, with summary calls counted apart.
def test_token_row_and_totals():
    calls = [{"node": "supervisor", "prompt_tokens": 900, "total_s": 1.0},
             {"node": "responder", "prompt_tokens": 700, "total_s": 1.5},
             {"node": "summary", "prompt_tokens": 400, "total_s": 3.0}]
    assert sc.token_row({"calls": calls}) == {"largest": 900, "responder": 700,
                                              "summary_tokens": 400, "summary_s": 3.0}
    totals = sc.token_totals([{"calls": calls}, {"calls": [
        {"node": "responder", "prompt_tokens": None, "total_s": 1.0}]}])
    assert totals == {"calls": 4, "all_prompt_tokens": 2000, "non_summary_prompt_tokens": 1600,
                      "unknown_token_counts": 1, "summary_calls": 1, "summary_s": [3.0]}
