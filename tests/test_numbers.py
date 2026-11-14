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
