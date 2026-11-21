"""Tests for the normalizer and the simple language tag (leo/language/normalize.py).

None of these sentences is a turn from an eval file.
"""

import pytest

from leo.language.normalize import has_joiner, language_tag, normalize


def test_short_spellings_are_fixed():
    assert normalize("kl subah kia plan hai") == "kal subah kya plan hai"
    assert normalize("Kl 9 bje mtg") == "kal 9 baje meeting"


def test_other_words_are_left_alone():
    assert normalize("Calendar check karo, please.") == "Calendar check karo, please."


@pytest.mark.parametrize("text", [
    "Parso Nashik jaana hai, ticket book karna yaad dilana",
    "Mujhe batao kal kya plan hai",
    "Sabzi wala task ho gaya",
    "Kitna time lagega?",
])
def test_hinglish_is_tagged_hinglish(text):
    assert language_tag(text, 0.2) == "hinglish"


@pytest.mark.parametrize("text", [
    "What do I have on Friday?",
    "Remind me to call the bank at noon",
    "Delete the note about the plumber",
    "How much is 12% of 900?",
])
def test_english_is_tagged_en(text):
    assert language_tag(text, 0.2) == "en"


def test_devanagari_is_tagged_hi_and_left_as_it_is():
    text = "कल बारिश होगी क्या?"
    assert language_tag(text, 0.2) == "hi"
    assert normalize(text) == text


def test_threshold_comes_from_config_by_default():
    assert language_tag("Mujhe batao kal kya plan hai") == "hinglish"


def test_joiners():
    assert has_joiner("Gym cancel karo aur call bhi")
    assert has_joiner("If it is sunny, add a picnic")
    assert has_joiner("Add eggs, bread to my tasks")
    assert not has_joiner("Kal 9 baje bank jaana hai")
