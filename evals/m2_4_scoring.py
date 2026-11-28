"""Pass rule and token figures for the M2.4 restart check (evals/m2_4_restart_check.py).

The pass rule is the user's, written in evals/scenarios/m2_4_restart_set.yaml
before any run:
  - R5 and R6 (recent) both answered;
  - at least 3 of R1-R4 (summarized) answered;
  - after the restart, the thread's state has a summary and the same last
    messages as just before the kill.
A turn is answered when its reply contains one of its expect_any_of keys
(case does not matter). Prompt tokens are reported only.
"""


# True when the reply contains one of the expected keys.
def answered(reply: str, keys: list[str]) -> bool:
    return any(k.lower() in reply.lower() for k in keys)


# Where the referred-back fact was when the question was asked: "recent" when its
# source line was still a message, "summary" when a key was in the summary, else "neither".
def where_found(turn: dict, source_text: str, keys: list[str]) -> str:
    if source_text in [text for _, text in turn["recent_before"]]:
        return "recent"
    return "summary" if answered(turn["summary_before"], keys) else "neither"


# The state check: a summary after the restart, and the same messages as before the kill.
def state_kept(before_kill: dict, after_restart: dict) -> bool:
    return bool(after_restart["summary"]) and after_restart["messages"] == before_kill["messages"]


# The pass rule, part by part: [(text, met)], from one variant's after-restart turns.
def pass_parts(rule: dict, turns: dict, before_kill: dict, after_restart: dict) -> list:
    recent = [answered(turns[i]["reply"], turns[i]["keys"]) for i in rule["recent_answered"]]
    summed = [answered(turns[i]["reply"], turns[i]["keys"]) for i in rule["summarized"]]
    need = rule["summarized_answered_min"]
    return [
        (f"R5 and R6 (recent) both answered: {sum(recent)} of {len(recent)}", all(recent)),
        (f"at least {need} of R1-R4 (summarized) answered: {sum(summed)} of {len(summed)}",
         sum(summed) >= need),
        (("after the restart the state has a summary and the same last messages as just "
         f"before the kill: {'yes' if state_kept(before_kill, after_restart) else 'no'}"),
         state_kept(before_kill, after_restart)),
    ]


# Per-turn prompt figures: the largest prompt of any call in the turn, the
# responder's prompt, and the summary call's tokens and time (None when absent).
def token_row(turn: dict) -> dict:
    sizes = [c["prompt_tokens"] for c in turn["calls"] if c["prompt_tokens"] is not None]
    responder = [c["prompt_tokens"] for c in turn["calls"] if c["node"] == "responder"]
    summary = [c for c in turn["calls"] if c["node"] == "summary"]
    return {"largest": max(sizes) if sizes else None,
            "responder": responder[-1] if responder else None,
            "summary_tokens": summary[0]["prompt_tokens"] if summary else None,
            "summary_s": summary[0]["total_s"] if summary else None}


# Totals for one variant: prompt tokens over every call (summary calls included,
# and without them), and the summary calls' count and times.
def token_totals(turns: list[dict]) -> dict:
    calls = [c for t in turns for c in t["calls"]]
    tokens = [c["prompt_tokens"] or 0 for c in calls]
    other = [c["prompt_tokens"] or 0 for c in calls if c["node"] != "summary"]
    times = [c["total_s"] for c in calls if c["node"] == "summary"]
    return {"calls": len(calls), "all_prompt_tokens": sum(tokens),
            "non_summary_prompt_tokens": sum(other),
            "unknown_token_counts": sum(c["prompt_tokens"] is None for c in calls),
            "summary_calls": len(times), "summary_s": times}
