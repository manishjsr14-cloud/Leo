"""Scoring for the M1.6 phrase sets (evals/scenarios/m1_6_*.yaml).

Used by evals/m1_6_parser_check.py (report) and tests/test_phrase_file.py.
A time case is correct only when every field in FIELDS matches; a number case
only on an exact match. Field defaults are the ones written in the YAML header.
"""

from datetime import datetime
from pathlib import Path

import yaml

from leo.language.numbers import NUMBER_WORDS, number_at, parse_amount, tokens
from leo.language.time_parser import parse_time, split_words
from leo.language.time_words import HOUR_MARKERS, UNITS

FIELDS = ["status", "date", "time", "assumed_ampm", "remind_before_min", "ask_about"]
DEFAULTS = {"status": "ok", "date": None, "time": None, "assumed_ampm": False,
            "remind_before_min": None, "ask_about": None}
# Number words that are also ordinary words: "do" (verb), "sat" (Saturday), ...
# parse_amount reads every number word, so in a number case any of these counts.
AMBIGUOUS = {"do", "sat", "che", "tin", "bara", "das", "ath"}


# Load one phrase set file.
def load_set(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# The expected fields of a time case, with the header defaults filled in.
def expected_fields(case: dict) -> dict:
    return {**DEFAULTS, **case["expect"]}


# The parser's answer as the same plain fields (dates and times as strings).
def got_fields(text: str, now: datetime) -> dict:
    result = parse_time(text, now).model_dump()
    got = {name: result[name] for name in FIELDS}
    got["date"] = got["date"].isoformat() if got["date"] else None
    got["time"] = got["time"].strftime("%H:%M") if got["time"] else None
    return got


# Number words the parser reads as an hour or a duration in this text.
def numbers_read(text: str) -> list[str]:
    words, read = split_words(text), []
    for i in range(len(words)):
        found = number_at(words, i)
        if found and found[1] < len(words) and (
                words[found[1]] in HOUR_MARKERS | {"am", "pm"} or words[found[1]] in UNITS):
            read += [x for x in words[i:found[1]] if x in NUMBER_WORDS]
    return read


# Score every case in a set; returns one row per case.
def score_set(data: dict) -> list[dict]:
    rows = []
    for case in data.get("times", []):
        now = datetime.fromisoformat(case.get("now", data["now"]))
        want, got = expected_fields(case), got_fields(case["text"], now)
        rows.append({"kind": "time", "id": case["id"], "text": case["text"],
                     "section": case.get("section"),
                     "now": now.strftime("%a %Y-%m-%d %H:%M"), "want": want, "got": got,
                     "ok": want == got,
                     "ambiguous_read": sorted(set(numbers_read(case["text"])) & AMBIGUOUS)})
    for case in data.get("numbers", []):
        got = parse_amount(case["text"])
        rows.append({"kind": "number", "id": case["id"], "text": case["text"], "now": "",
                     "section": case.get("section"),
                     "want": case["expect"], "got": got, "ok": got == case["expect"],
                     "ambiguous_read": sorted(set(tokens(case["text"])) & AMBIGUOUS)})
    return rows


# Accuracy as (correct, total).
def accuracy(rows: list[dict]) -> tuple[int, int]:
    return sum(r["ok"] for r in rows), len(rows)
