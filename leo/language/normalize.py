"""Normalizer and simple language tag (architecture section 15.2, M1.8).

normalize(text): fixes common short spellings ("kl" -> "kal", "kia" -> "kya").
language_tag(text): "hi" when the text is mostly Devanagari, "hinglish" when at
least language.hinglish_min_ratio of its words are common Hindi words written
in Roman script, else "en". This is the simple token-ratio tag of M1.8; the
trained detector comes in Phase 6 (section 8.2). Devanagari input is tagged
"hi" and left as it is (no transliteration in M1.8).
has_joiner(text): True when the message links more than one request ("aur",
"and", "agar", a comma ...); the agents then never finish early.
"""

import re

from leo.config import load_config

# Short spellings -> the spelling the rest of Leo knows. Whole words only.
SPELLINGS = {"kl": "kal", "kia": "kya", "kyaa": "kya", "nhi": "nahi", "nai": "nahi",
             "tmrw": "tomorrow", "tmr": "tomorrow", "pls": "please", "plz": "please",
             "mtg": "meeting", "bje": "baje"}

# Common Hindi words in Roman script. English look-alikes ("me", "do", "to",
# "the", "hi", "par", "mat", "minute") are left out on purpose.
HINDI_WORDS = {
    "hai", "hain", "tha", "thi", "ho", "hoon", "hun", "hoga", "hogi", "hua", "hui",
    "kya", "kyun", "kaise", "kab", "kahan", "kitna", "kitne", "kaun", "kaunsa", "kis",
    "mera", "meri", "mere", "mujhe", "aap", "aapka", "aapki", "tum", "tera", "uska",
    "ka", "ki", "ke", "ko", "se", "mein", "pe", "tak", "liye", "saath", "wala", "wali",
    "aur", "ya", "bhi", "nahi", "nahin", "haan", "ji", "accha", "acha", "theek",
    "kar", "karo", "karna", "kardo", "karde", "kiya", "dena", "diya", "daal",
    "dalo", "rakh", "rakho", "laga", "lagao", "likh", "likho", "lo", "batao", "bata",
    "dikhao", "hatao", "hata", "chahiye", "jaana", "jana", "aana", "chalo", "sakta",
    "kal", "aaj", "parso", "subah", "dopahar", "shaam", "raat", "baje", "abhi", "baad",
    "pehle", "ghanta", "baarish", "dhoop", "ek", "doodh", "sabzi", "agar",
    "toh", "lekin", "kuch", "sab", "koi", "yeh", "woh", "wahan", "yahan", "matlab",
}
JOINERS = {"aur", "and", "phir", "then", "also", "agar", "if", "plus"}
DEVANAGARI = re.compile(r"[ऀ-ॿ]")


# Replace the short spellings, keeping everything else as it is.
def normalize(text: str) -> str:
    return re.sub(r"[A-Za-z]+", lambda m: SPELLINGS.get(m.group(0).lower(), m.group(0)),
                  text)


# The Roman-script words of a text, lowercase.
def roman_words(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


# "hi", "hinglish" or "en" for one message (see the module comment).
def language_tag(text: str, min_ratio: float | None = None) -> str:
    devanagari = len(DEVANAGARI.findall(text))
    words = roman_words(text)
    if devanagari and devanagari >= sum(len(w) for w in words):
        return "hi"
    if not words:
        return "en"
    ratio = min_ratio if min_ratio is not None else load_config().language.hinglish_min_ratio
    hindi = sum(1 for w in words if w in HINDI_WORDS)
    return "hinglish" if hindi / len(words) >= ratio else "en"


# True when the message links two or more requests.
def has_joiner(text: str) -> bool:
    return "," in text or ";" in text or bool(set(roman_words(text)) & JOINERS)
