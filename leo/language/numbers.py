"""Indian number words in Roman Hinglish (architecture 15.2, task M1.6).

Reads amounts like "dedh sau" (150), "paune do lakh" (175000) and "₹1,50,000".
The time parser reuses `number_at` for hours such as "sava teen" (3.25).
Rules only, no LLM. Fractions are exact (fractions.Fraction), never floats.
"""

import re
from fractions import Fraction

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


# Parse an amount in rupees ("dhai lakh", "3 lakh 50 hazaar", "Rs 2.5 lakh").
# Returns a whole number, or None when the text holds no amount or the
# amount is not a whole number of rupees.
def parse_amount(text: str) -> int | None:
    words = [w for w in tokens(text) if w not in CURRENCY]
    total, found, i = Fraction(0), False, 0
    while i < len(words):
        read = number_at(words, i)
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
