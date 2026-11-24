"""Scorer v2 for eval records (M1 cleanup item 2).

Adds the language check of evals/language_scoring_v2.py to one scored turn
record, next to v1's: lang_v2_ok, lang_v2_why, passed_v2 and verdict_v2.
Every other check (routing, tools, reply rules) is the record's own, so v1
and v2 differ only in the language check. Works on new records from
evals/run_eval.py and on records loaded from an earlier report's .json, so a
stored run (such as the M1.10 baseline) can be rescored without running the
model again; the stored file itself is never changed.
"""

from evals.eval_scoring import verdict
from evals.language_scoring_v2 import language_ok_v2


# The tool results of a turn as one text, as evals/m1_8_check.run_one builds it for v1.
def tool_text(steps: list[dict]) -> str:
    return " ".join(str(s.get("result")) for s in steps)


# A copy of the record with the v2 language check, pass and verdict added.
def with_v2(record: dict) -> dict:
    ok, why = language_ok_v2(record["reply"], record["lang"], tool_text(record["steps"]))
    passed = (record["routing_ok"] and record["tools_ok"] is not False
              and ok and not record["reply_fails"])
    return {**record, "lang_v2_ok": ok, "lang_v2_why": why, "passed_v2": passed,
            "verdict_v2": verdict(passed, record["known"])}


# The reasons a turn failed, with the chosen scorer's language reason first.
def fail_reasons(record: dict, scorer: str = "v1") -> list[str]:
    ok, why = ((record["lang_ok"], record["lang_why"]) if scorer == "v1"
               else (record["lang_v2_ok"], record["lang_v2_why"]))
    reasons = [] if ok else [f"language ({scorer}): {why}"]
    if not record["routing_ok"]:
        reasons.append(f"plan {record['plan']}")
    return reasons + record["tool_fails"] + record["reply_fails"]
