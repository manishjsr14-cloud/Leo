"""Indian number words in Roman Hinglish (architecture 15.2, task M1.6).

Reads amounts like "dedh sau" (150), "paune do lakh" (175000) and "₹1,50,000".
The time parser reuses `number_at` for hours such as "sava teen" (3.25).
Rules only, no LLM. Fractions are exact (fractions.Fraction), never floats.
M1 cleanup item 5: amounts also read the words 13-99 (number_words.py) and
"sau"/"hazaar" alone; clock hours (number_at) still know only one to twelve.
"""

import re
from fractions import Fraction

from leo.language.number_words import ALSO_WORDS, AMOUNT_WORDS

# Number words one to twelve, with common Roman spellings.
WORDS = {
    1: ["ek"], 2: ["do"], 3: ["teen", "tin"], 4: ["chaar", "char"],
    5: ["paanch", "panch", "paach"], 6: ["chhe", "che", "chhah", "chah", "chheh"],
    7: ["saat", "sat"], 8: ["aath", "ath"], 9: ["nau", "nao"], 10: ["das", "dus"],
    11: ["gyarah", "gyaarah", "gyara", "gyaara"], 12: ["barah", "baarah", "bara", "baara"],
}
NUMBER_WORDS = {spelling: Fraction(n) for n, spellings in WORDS.items() for spelling in spellings}

# Words that are a whole value on their own: dedh = 1.5, dhai = 2.5, aadha = 0.5.
WHOLE_FRACTIONS = {
    **dict.fromkeys(["dedh", "derh"], Fraction(3, 2)),
    **dict.fromkeys(["dhai", "dhaai", "dhaee", "adhai", "dhaayi"], Fraction(5, 2)),
    **dict.fromkeys(["aadha", "aadhe", "adha", "adhe", "aadhi"], Fraction(1, 2)),
}

# Words that change the number after them: sava +1/4, saadhe +1/2, paune -1/4.
MODIFIERS = {
    **dict.fromkeys(["sava", "sawa", "savva"], Fraction(1, 4)),
    **dict.fromkeys(["saadhe", "sadhe", "saade", "sade"], Fraction(1, 2)),
    **dict.fromkeys(["paune", "pone", "paone", "pauney"], Fraction(-1, 4)),
}

# Words that multiply the number before them.
MULTIPLIERS = {
    "sau": 100,
    **dict.fromkeys(["hazaar", "hazar", "hajaar", "hajar", "thousand"], 1000),
    **dict.fromkeys(["lakh", "lakhs", "lac", "laakh"], 100_000),
    **dict.fromkeys(["crore", "crores", "cr", "karod", "karor"], 10_000_000),
}

# "sau" and "hazaar" (any spelling) also count with no number before them.
ALONE_VALUES = {100, 1000}

DIGITS = re.compile(r"^\d+(\.\d+)?$")
# Words that only say "rupees" and carry no value.
CURRENCY = {"₹", "rs", "rs.", "inr", "rupaye", "rupees", "rupee", "rupay", "rupaiye"}


# Split text into lowercase words; "₹1,50,000" becomes ["₹", "150000"].
def tokens(text: str) -> list[str]:
    text = text.lower().replace("₹", " ₹ ")
    text = re.sub(r"(?<=\d),(?=\d)", "", text)       # Indian digit grouping
    return re.findall(r"₹|\d+(?:\.\d+)?|[a-z.]+", text)


# The value of one plain number word or digit string, or None.
def plain_value(word: str) -> Fraction | None:
    if DIGITS.match(word):
        return Fraction(word)
    return NUMBER_WORDS.get(word, WHOLE_FRACTIONS.get(word))


# Read one number starting at words[i]: "teen", "12", "dedh", "sava teen", or a
# modifier on its own before a multiplier ("sava sau" = 1.25 x 100).
# Returns (value, index after it), or None when no number starts there.
def number_at(words: list[str], i: int) -> tuple[Fraction, int] | None:
    if i >= len(words):
        return None
    word = words[i]
    if word in MODIFIERS:
        base = plain_value(words[i + 1]) if i + 1 < len(words) else None
        if base is None:
            return Fraction(1) + MODIFIERS[word], i + 1
        return base + MODIFIERS[word], i + 2
    value = plain_value(word)
    return (value, i + 1) if value is not None else None


# Read one number of an amount at words[i]: what number_at reads, a word from
# 13 to 99 (number_words.py), or "sau"/"hazaar" with no number before it (read
# as 1, the multiplier is applied next). "saath"/"sath" counts only right before
# a multiplier or a rupee word. Returns (value, index after it) or None.
def amount_at(words: list[str], i: int) -> tuple[Fraction, int] | None:
    read = number_at(words, i)
    if read is not None:
        return read
    word = words[i]
    after = words[i + 1] if i + 1 < len(words) else ""
    if word in ALSO_WORDS and after not in MULTIPLIERS and after not in CURRENCY:
        return None
    if word in AMOUNT_WORDS:
        return Fraction(AMOUNT_WORDS[word]), i + 1
    if MULTIPLIERS.get(word) in ALONE_VALUES:
        return Fraction(1), i
    return None


# Parse an amount in rupees ("dhai lakh", "3 lakh 50 hazaar", "Rs 2.5 lakh",
# "pachaas hazaar"). Returns a whole number, or None when the text holds no
# amount or the amount is not a whole number of rupees.
def parse_amount(text: str) -> int | None:
    words = tokens(text)                             # rupee words kept: "saath rupaye"
    total, found, i = Fraction(0), False, 0
    while i < len(words):
        read = None if words[i] in CURRENCY else amount_at(words, i)
        if read is None:
            i += 1                                   # skip words that are not numbers
            continue
        value, i = read
        if i < len(words) and words[i] in MULTIPLIERS:
            value *= MULTIPLIERS[words[i]]
            i += 1
        total += value
        found = True
    if not found or total.denominator != 1:
        return None
    return int(total)
