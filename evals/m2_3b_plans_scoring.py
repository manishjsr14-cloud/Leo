"""Scoring for the M2.3b plan-rule follow-up check (evals/scenarios/m2_3b_plans_set.yaml).

For each message it names WHICH rule of the real write path
(leo/graph/memory_nodes.py, memory_write_node) keeps it out, in that node's
order: the question rule, then the write trigger (no first-person word, a
request word, small talk), then the plan rule. It also says whether the plan
rule alone would keep it out, so a plan kept out only by another rule is
visible. Whether a message was stored is read from the run (a memory row
created during its turn), never from these rules.
"""

from datetime import datetime

from leo.language.memory_events import is_plan_or_event, plan_reason
from leo.language.memory_words import (
    fact_text,
    first_person,
    is_question,
    is_request,
    is_small_talk,
    says_remember,
)


# The first rule of the write path that keeps the message out, or None.
def kept_out_by(text: str, now: datetime) -> str | None:
    if is_question(text):
        return "question rule"
    if not says_remember(text):
        if not first_person(text):
            return "no first-person word"
        if is_request(text):
            return "request word"
        if is_small_talk(text):
            return "small talk"
    return plan_rule(text, now)


# "plan rule (<part>)" when the plan rule alone keeps the message out, else None.
def plan_rule(text: str, now: datetime) -> str | None:
    fact = fact_text(text)
    return f"plan rule ({plan_reason(fact, now)})" if is_plan_or_event(fact, now) else None


# The pass-rule parts: (text, met) for the plans and the facts.
def parts(rule: dict, data: dict, records: dict) -> list[tuple[str, bool]]:
    plans = [m["id"] for m in data["plans"] if records[m["id"]]["created"]]
    facts = [m["id"] for m in data["facts"] if records[m["id"]]["created"]]
    missing = [m["id"] for m in data["facts"] if m["id"] not in facts]
    plan_text = (f"plans stored: {len(plans)} of {len(data['plans'])} "
                 f"(max {rule['plans_stored_max']}; stored: {plans or 'none'})")
    fact_text_ = (f"facts stored: {len(facts)} of {len(data['facts'])} "
                  f"(min {rule['facts_stored_min']}; not stored: {missing or 'none'})")
    return [(plan_text, len(plans) <= rule["plans_stored_max"]),
            (fact_text_, len(facts) >= rule["facts_stored_min"])]
