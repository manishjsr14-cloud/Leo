"""Tests for the reply language scorer v2 (evals/language_scoring_v2.py).
Cases here are not taken from the check set, so the check set stays a check."""

from evals.language_scoring_v2 import language_ok_v2, reply_language
from evals.m1_cleanup_scorer_check import score_case


def test_devanagari_majority_is_hi():
    assert reply_language("कल मीटिंग है, Rahul के साथ")[0] == "hi"


def test_some_devanagari_in_a_roman_reply_is_unclear():
    assert reply_language("Your meeting with Rahul tomorrow is at ten, ठीक")[0] == "unclear"


def test_two_markers_make_hinglish():
    assert reply_language("Please wait, abhi check kar raha")[0] == "hinglish"


def test_one_marker_in_a_short_reply_is_hinglish_by_ratio():
    assert reply_language("Sab set.")[0] == "hinglish"


def test_one_marker_in_a_long_english_reply_is_unclear():
    reply = "I moved your dentist visit to Friday evening and also sent the list, ji"
    assert reply_language(reply)[0] == "unclear"


def test_no_marker_is_english():
    assert reply_language("Your timer is running.") == ("en", [])


def test_english_look_alikes_are_not_markers():
    assert reply_language("Do you want me to put the main item on hold?")[0] == "en"


def test_tool_data_words_are_not_counted():
    reply = "Added 'Bhai ka kaam karna hai' to your notes."
    assert reply_language(reply)[0] != "en"
    assert reply_language(reply, "Bhai ka kaam karna hai")[0] == "en"


def test_reply_with_only_tool_data_and_numbers_is_english():
    assert reply_language("Chai: 10", "Chai")[0] == "en"


def test_language_ok_v2_passes_only_the_named_language():
    assert language_ok_v2("Theek hai, abhi bata deta", "hinglish")[0]
    assert not language_ok_v2("Theek hai, abhi bata deta", "en")[0]
    passed, why = language_ok_v2("All set for today.", "hinglish")
    assert not passed and "v2 language en" in why


def test_check_script_gives_v1_no_result_for_hi_cases():
    row = score_case({"id": "x", "label": "hi", "tool_data": "", "reply": "ठीक है"})
    assert row["v1"] == "n/a" and row["v2_ok"]
