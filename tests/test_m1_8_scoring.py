"""Tests for the M1.8 check scorer (evals/m1_8_scoring.py, evals/m1_8_times.py)."""

from pathlib import Path

import pytest
import yaml

from evals.m1_8_check_helpers import baseline_calls
from evals.m1_8_scoring import language_ok, reply_fails
from evals.m1_8_times import reply_times

# One tool step whose result holds an event at 17:00-18:00.
STEPS = [{"tool": "get_events", "args": {"start": "2026-11-16T00:00:00+05:30"},
          "result": [{"title": "Review call", "start": "2026-11-16T17:00:00+05:30",
                      "end": "2026-11-16T18:00:00+05:30"}]}]
TURN = {"text": "Aaj shaam 5 baje kya hai?"}


# Clock-time rule failures only.
def clock_fails(reply: str, steps=STEPS) -> list[str]:
    return [f for f in reply_fails(reply, TURN, steps) if f.startswith("clock_times")]


@pytest.mark.parametrize("reply", [
    "Review call at 17:00.",
    "Review call at 5 pm.",
    "Review call at 5:00 PM.",
    "Shaam 5 baje Review call hai.",
    "Review call 5-6 pm hai.",
    "Review call 5:00 to 6:00 p.m.",
    "Review call shaam 5 se 6 baje tak hai.",
    "Review call shaam paanch baje hai.",
])
def test_each_form_of_17_00_matches(reply):
    assert clock_fails(reply) == []


def test_a_different_time_fails():
    assert clock_fails("Review call at 7 pm.") != []
    assert clock_fails("Review call at 19:00.") != []
    assert clock_fails("Subah 5 baje Review call hai.") != []


def test_invented_end_of_range_fails():
    # 17:00 shown as "5-7 PM" (an M1.7 reply): 7 pm is not in the results.
    assert clock_fails("Review call 5-7 PM hai.") != []


def test_time_with_no_am_pm_may_be_either():
    assert clock_fails("Review call 5 baje hai.") == []
    assert clock_fails("Review call 5:00 hai.") == []


def test_plain_numbers_are_not_times():
    assert reply_times("10 minute ka timer, 18% of 2450 is 441, Tue 17 Nov") == []


def test_hindi_fractions_read_as_times():
    steps = [{"tool": "x", "args": {}, "result": {"start": "2026-11-16T18:30:00+05:30"}}]
    assert clock_fails("Shaam saadhe 6 baje.", steps) == []
    assert clock_fails("Shaam sava 6 baje.", steps) != []


def test_required_times_and_forbidden_words():
    turn = {"text": "x", "reply_times_required": ["17:00"], "reply_forbid": ["already"],
            "reply_must_mention": ["Review"]}
    assert reply_fails("Review call 5 pm pe hai.", turn, STEPS) == []
    fails = reply_fails("Task is already done.", turn, STEPS)
    assert any(f.startswith("reply_times_required") for f in fails)
    assert any(f.startswith("reply_forbid") for f in fails)
    assert any(f.startswith("reply_must_mention") for f in fails)


def test_json_in_words_and_devanagari_fail():
    fails = reply_fails('{"id": 6} In words: नहीं', TURN, [])
    assert {f.split(":")[0] for f in fails} >= {"no_json", "no_in_words", "no_devanagari"}


def test_language_rules():
    assert language_ok("Ho gaya, task complete kar diya.", "hinglish")[0]
    assert not language_ok("Done, the task is complete.", "hinglish")[0]
    assert not language_ok("नहीं, बारिश नहीं होगी।", "hinglish")[0]
    assert language_ok("Done, the task is complete.", "en")[0]
    assert not language_ok("Task complete kar diya hai.", "en")[0]
    # Words that come from the tool data (a title) do not count against English.
    assert language_ok("Your event 'Milna ke baad' is on.", "en", "Milna ke baad")[0]


def test_baseline_calls_reads_the_turn_table(tmp_path: Path):
    report = tmp_path / "r.md"
    report.write_text("# x\n\n| turn | lang | llm_calls |\n|---|---|---|\n"
                      "| L01 | hinglish | 4 |\n| L02 | en | 3 |\n", encoding="utf-8")
    assert baseline_calls(report) == {"L01": 4, "L02": 3}


def test_turn_file_shape():
    data = yaml.safe_load(Path("evals/scenarios/m1_8_language_turns.yaml").read_text("utf-8"))
    language = [t for t in data["turns"] if t["id"].startswith("L")]
    assert len(language) == 20
    assert sum(t["lang"] == "hinglish" for t in language) >= 10
    assert len({t["id"] for t in data["turns"]}) == len(data["turns"])
    assert all(t["lang"] in ("en", "hinglish") and "expect" in t for t in data["turns"])
