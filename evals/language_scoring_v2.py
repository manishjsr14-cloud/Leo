"""Reply language scorer v2 (M1 cleanup item 1). v1 (evals/m1_8_scoring.py
language_ok) stays as it is; reports show both.

v1 needs at least 2 Hindi markers for a Hinglish reply, so a short valid
reply like "Hi! Baat karein, kaise ho?" fails (M1 exit run6, L20). v2 names
the reply's language, by this rule (fixed in IMPLEMENTATION_PLAN.md before
the check set evals/scenarios/m1_cleanup_language_replies.yaml was written):
  1. "hi" when the reply has at least as many Devanagari letters as Roman ones;
     any other reply with Devanagari is "unclear" (mixed script);
  2. words that appear in the turn's tool data (titles, places) are dropped;
  3. "hinglish" when at least 2 of the remaining words are Hindi markers, or
     markers are at least 20 % of them;
  4. "en" when none is a marker; anything else is "unclear".
A reply passes when its language is the one expected; "unclear" fails both.
Markers: v1's list plus common Hindi verb forms, question words and pronoun
forms in Roman script. English look-alikes ("main", "me", "do", "to", "hi",
"par", "so", "are", "the") are left out on purpose. Fixed with this version.
"""

import re

from evals.m1_8_scoring import HINDI_MARKERS as V1_MARKERS

MARKERS = V1_MARKERS | {
    # question words
    "kaise", "kaisa", "kaisi", "kab", "kahan", "kyun", "kyon", "kaun", "kitna",
    "kitne", "kitni",
    # verb forms
    "karein", "karen", "kijiye", "karunga", "karungi", "karte", "karti", "karta",
    "karne", "karni", "hoon", "hun", "tha", "thi", "batao", "bataiye",
    "batayein", "dijiye", "lijiye", "liya", "liye", "mila", "mili", "mile",
    "chahte", "chahti", "chahta", "rahega", "rahegi", "baat", "dekho", "dekhiye",
    # pronoun forms
    "mujhe", "mera", "meri", "mere", "aapko", "aapse", "tumhe", "tumhara", "hum",
    "hamara", "uska", "uski", "unka", "isliye",
}
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
ROMAN = re.compile(r"[A-Za-z]")
RATIO = 0.2


# The lowercase Roman-script words of a text.
def words(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


# The reply's language: "en", "hinglish", "hi" or "unclear", with the markers found.
def reply_language(reply: str, tool_text: str = "") -> tuple[str, list[str]]:
    devanagari, roman = len(DEVANAGARI.findall(reply)), len(ROMAN.findall(reply))
    if devanagari and devanagari >= roman:
        return "hi", []
    if devanagari:
        return "unclear", []
    data = set(words(tool_text))
    counted = [w for w in words(reply) if w not in data]
    markers = [w for w in counted if w in MARKERS]
    if not markers:
        return "en", markers
    if len(markers) >= 2 or len(markers) / len(counted) >= RATIO:
        return "hinglish", markers
    return "unclear", markers


# Language check v2: (passed, why), the same shape as v1's language_ok.
def language_ok_v2(reply: str, lang: str, tool_text: str = "") -> tuple[bool, str]:
    found, markers = reply_language(reply, tool_text)
    return found == lang, f"v2 language {found}, Hindi markers: {markers}"
