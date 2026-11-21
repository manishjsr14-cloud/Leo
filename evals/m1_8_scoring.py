"""Scoring for evals/m1_8_check.py, following the header of
evals/scenarios/m1_8_language_turns.yaml.

Language and reply rules are written here, apart from Leo's own code, so the
check does not grade Leo with its own detector. The Hindi marker list below is
fixed with the turn file and is not changed to improve a score.
Tool checks reuse the M1.7 scorer (evals/m1_7_scoring.py).
"""

import json
import re

from evals.m1_7_scoring import score_turn
from evals.m1_8_times import minutes_of, reply_times

# Common Hindi words written in Roman script. English look-alikes ("me", "do",
# "to", "par", "hi") are left out on purpose.
HINDI_MARKERS = {
    "hai", "hain", "ho", "hoga", "hogi", "hoge", "hua", "hui", "gaya", "gayi", "gaye",
    "diya", "diye", "di", "kar", "karna", "karo", "kiya", "ke", "ka", "ki", "ko",
    "mein", "nahi", "nahin", "aap", "aapka", "aapki", "aapke", "tum", "haan", "ji",
    "raha", "rahi", "rahe", "liye", "wala", "wali", "baje", "kal", "aaj", "se", "tak",
    "bhi", "abhi", "kya", "kuch", "sab", "theek", "thik", "accha", "acha", "chahiye",
    "dunga", "dungi", "lagaya", "daal", "daala", "sakta", "sakti", "sakte", "koi", "aur",
    "pe", "toh", "matlab", "bilkul", "zaroor", "wahi", "yeh", "ye", "woh", "agar", "lekin",
}
DEVANAGARI = re.compile(r"[ऀ-ॿ]")


# The lowercase words of a text (letters only).
def words(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


# True when the text has any Devanagari letter.
def has_devanagari(text: str) -> bool:
    return DEVANAGARI.search(text) is not None


# Language check: (passed, why). `tool_text` holds the turn's tool results, whose
# words (titles, places) are not counted against an English reply.
def language_ok(reply: str, lang: str, tool_text: str = "") -> tuple[bool, str]:
    if has_devanagari(reply):
        return False, "Devanagari in the reply"
    data_words = set(words(tool_text))
    markers = [w for w in words(reply) if w in HINDI_MARKERS]
    if lang == "hinglish":
        return (len(markers) >= 2, f"Hindi markers: {markers}")
    outside = [w for w in markers if w not in data_words]
    return (not outside, f"Hindi markers outside tool data: {outside}")


# Every clock time ("HH:MM") inside the tool calls and results of a turn.
def allowed_minutes(steps: list[dict]) -> set[int]:
    text = json.dumps([[s.get("args"), s.get("result")] for s in steps], default=str)
    return {int(h) * 60 + int(m) for h, m in re.findall(r"T(\d{2}):(\d{2})", text)}


# Reply rules for one turn. Returns the list of failed rules with reasons.
def reply_fails(reply: str, turn: dict, steps: list[dict]) -> list[str]:
    fails, low = [], reply.lower()
    if has_devanagari(reply) and not has_devanagari(turn["text"]):
        fails.append("no_devanagari: Devanagari reply to a Roman-script message")
    if "{" in reply or '":' in reply:
        fails.append("no_json: the reply holds JSON-like text")
    if "in words" in low:
        fails.append("no_in_words: the reply copies the 'In words' line")
    allowed = allowed_minutes(steps)
    bad = [found for found, options in reply_times(reply) if not options & allowed]
    if bad:
        fails.append(f"clock_times: not in the tool results: {bad}")
    for word in turn.get("reply_forbid", []):
        if word.lower() in low:
            fails.append(f"reply_forbid: says {word!r}")
    for word in turn.get("reply_must_mention", []):
        if word.lower() not in low:
            fails.append(f"reply_must_mention: does not mention {word!r}")
    said = set().union(*[options for _, options in reply_times(reply)])
    for clock in turn.get("reply_times_required", []):
        if minutes_of(clock) not in said:
            fails.append(f"reply_times_required: {clock} not mentioned")
    return fails


# The tool checks for one turn (M1.7 rules). Returns the list of failures.
def tool_fails(turn: dict, plan, steps: list[dict], executed: list[str],
               stops: dict[str, str]) -> list[str]:
    return score_turn(turn["expect"], plan, steps, executed, stops)[1]


# True when every expected call of the turn was attempted (for multi_step turns).
def all_calls_attempted(fails: list[str]) -> bool:
    return not any(f.startswith("missing call") for f in fails)
