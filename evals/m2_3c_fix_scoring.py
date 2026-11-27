"""Scoring for the M2.3c fix-round set (evals/scenarios/m2_3c_fixround_set.yaml).

Tool counts come from each turn's mock tools' log. For an offer, the date
shown must be the date the Indian time parser reads at the set's "now" (with
its clock time when it read one), and the reply must hold the offer words of
the turn's language (prompts/replies.yaml, calendar_offer). For an ask, the
reply must be the parser's question, word for word.
"""

from datetime import datetime

from evals.m2_3c_scoring import ran_ok
from leo.language.say_time import say_clock, say_day
from leo.language.time_parser import parse_time
from leo.llm.prompts import load_prompt


# Why an event statement's reply fails its rule, or None when it passes.
def event_miss(message: dict, record: dict, now: datetime) -> str | None:
    reply, parsed = record["reply"], parse_time(message["text"], now)
    if record["tool_log"]:
        return f"{len(record['tool_log'])} tool calls"
    if message["expect"] == "ask":
        return None if parsed.status == "ask" and reply == parsed.question else "not the question"
    if parsed.status != "ok":
        return f"parser status {parsed.status}"
    shown = say_day(parsed.date) + (f", {say_clock(parsed.time)}" if parsed.time else "")
    words = load_prompt("replies").extra(message["lang"])["calendar_offer"].split("{when}")[1]
    if shown not in reply:
        return f"parser's date '{shown}' not shown"
    return None if words in reply else "no offer words"


# The fix-round pass-rule parts: (text, met).
def fix_parts(data: dict, records: dict, now: datetime) -> list[tuple[str, bool]]:
    events = {m["id"]: event_miss(m, records[m["id"]], now) for m in data["event_statements"]}
    misses = {k: v for k, v in events.items() if v}
    calls = {m["id"]: len(records[m["id"]]["tool_log"]) for m in data["first_person_statements"]}
    called = {k: v for k, v in calls.items() if v}
    missed = [m["id"] for m in data["requests"]
              if not ran_ok(records[m["id"]]["tool_log"], m["expect_write"])]
    return [
        ((f"event statements: offer with the parser's date, or the parser's question, and 0 "
         f"tool calls for {len(events) - len(misses)} of {len(events)} (missed: "
         f"{misses or 'none'})"), not misses),
        ((f"'I + request word' statements: {sum(calls.values())} tool calls (max 0; by message: "
         f"{called or 'none'})"), not called),
        ((f"requests: expected write call ran for {len(data['requests']) - len(missed)} of "
         f"{len(data['requests'])} (missed: {missed or 'none'})"), not missed),
    ]
