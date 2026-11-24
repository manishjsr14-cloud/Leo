"""Tests for leo/language/numbers.py: Indian number words, lakh/crore and ₹.

These are rule-by-rule checks. The frozen phrase set
(evals/scenarios/m1_6_indian_phrases.yaml) is scored separately.
"""

from fractions import Fraction

import pytest

from leo.language.numbers import number_at, parse_amount, tokens


@pytest.mark.parametrize(
    ("text", "amount"),
    [
        ("teen sau", 300),            # plain word x multiplier
        ("dedh sau", 150),            # dedh = 1.5
        ("dhai hazaar", 2500),        # dhai = 2.5
        ("sava sau", 125),            # modifier with no number = 1 + 1/4
        ("saadhe chaar lakh", 450000),
        ("paune teen crore", 27500000),
        ("2 crore 50 lakh", 25000000),  # groups add up
        ("1.5 lakh", 150000),
        ("₹2,45,000", 245000),        # Indian digit grouping
        ("RS. 500", 500),
        ("700 rupaye", 700),
        ("gyarah sau", 1100),
        ("12", 12),
    ],
)
# Each rule gives the expected whole-rupee amount.
def test_parse_amount(text, amount):
    assert parse_amount(text) == amount


@pytest.mark.parametrize("text", ["", "kuch nahi", "paise chahiye", "dedh"])
# No number, or a value that is not whole rupees (dedh = 1.5), gives None.
def test_parse_amount_none(text):
    assert parse_amount(text) is None


# Spelling variants map to the same value.
def test_spelling_variants():
    assert parse_amount("sade teen hajar") == parse_amount("saadhe teen hazaar") == 3500
    assert parse_amount("derh lac") == 150000
    assert parse_amount("pone do sau") == 175


# number_at reads hours for the time parser and says where it stopped.
def test_number_at():
    words = ["sava", "teen", "baje"]
    assert number_at(words, 0) == (Fraction(13, 4), 2)
    assert number_at(["paune", "ek"], 0) == (Fraction(3, 4), 2)
    assert number_at(["dhai", "baje"], 0) == (Fraction(5, 2), 1)
    assert number_at(["baje"], 0) is None
    assert number_at([], 0) is None


# tokens splits ₹ off and removes commas only between digits.
def test_tokens():
    assert tokens("₹1,50,000 de do") == ["₹", "150000", "de", "do"]
    assert tokens("haan, theek") == ["haan", "theek"]


# M1 cleanup item 5: words 13-99 in amounts (cases not taken from the phrase file).
def test_words_from_13_to_99_in_amounts():
    assert parse_amount("athara hazaar") == 18000
    assert parse_amount("bayalis rupaye") == 42
    assert parse_amount("navve lakh") == 9000000
    assert parse_amount("ek hazaar teis") == 1023


def test_saath_is_60_only_before_a_multiplier_or_rupee_word():
    assert parse_amount("sath sau") == 6000
    assert parse_amount("Rs saath") is None          # a rupee word BEFORE it does not count
    assert parse_amount("mummy ke saath") is None


def test_sau_and_hazaar_alone():
    assert parse_amount("hazaar") == 1000
    assert parse_amount("sau aur pachas") == 150
    assert parse_amount("lakh") is None              # only sau and hazaar stand alone


def test_words_above_twelve_are_never_clock_hours():
    assert number_at(["bees", "baje"], 0) is None
    assert number_at(["pachaas"], 0) is None
