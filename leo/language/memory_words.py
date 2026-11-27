"""Word rules for long-term memory (M2.3, redesigned in M2.3b).

Most turns are requests and questions, so memory_write must not add an LLM call
to every turn. These rules run first, in code.

Write trigger (M2.3b): a message is a candidate memory when it is not a
question and either says "remember" / "yaad rakhna", or is a first-person
statement (I, me, my, main, mera, mujhe, ...) with no request word (the M2.3b
fix round added complete, mark, remove, list, open, reschedule, rename and
update: "complete my milk task" in the M1.10 suite would have been stored). Plans and
events are kept out by leo/language/memory_events.py.

Update cue (M2.3b): only a message with an explicit update word replaces an
older memory: anymore, no longer, moved to, chhod di / diya, ab ... nahi.
Without a cue, a fact on a known topic is added next to the old one.

Personal-question gate (M2.3b): recall gives hints only for a question with a
first-person word ("What's my ...", "Do I ...", "Mujhe kis ...", "Main ... ?").

The word lists were fixed in the approved M2.3b proposal, after reading the
check set (evals/scenarios/m2_3b_memory_set.yaml). M2.3b follow-up (the user's
rule): "is" is also Hinglish for "this" ("Is saal se ..."), so it is not a
question start; a message that starts with it is a question only when it ends
in "?" ("Is my dentist visit tomorrow?").
"""

import re

REMEMBER = re.compile(r"^\s*(yaad rakh lo|yaad rakhna|yaad rakho|remember that|remember)\b"
                      r"[\s,:;.!-]*", re.IGNORECASE)
REMEMBER_AT_END = re.compile(r"[\s,;-]*\b(yaad rakh lo|yaad rakhna|yaad rakho|remember that)"
                             r"\s*[.!]*\s*$", re.IGNORECASE)
# "is" left out on purpose (M2.3b follow-up): see the module note.
QUESTION_START = {"what", "when", "where", "who", "which", "how", "why", "do", "does", "did",
                  "am", "are", "can"}
HINGLISH_QUESTION = {"kya", "kab", "kahan", "kaun", "kaunsa", "kaunsi", "kitna", "kitne", "kitni",
                     "kaise", "kyun", "kyon"}
FIRST_PERSON = {"i", "i'm", "i've", "i'd", "i'll", "me", "my", "mine", "myself", "main", "maine",
                "mera", "meri", "mere", "mujhe", "mujhko"}
REQUEST = re.compile(
    r"\b(remind|yaad dila\w*|batao|bata do|bataiye|dikhao|dikha do|show|tell me|set|add|daal"
    r"|daalo|dal do|cancel|delete|hatao|hata do|karo|kar do|kardo|please|plz|search|dhundo"
    r"|find|check|schedule|create|lagao|laga do|chahiye|calculate|convert|note kar"
    r"|complete|mark|remove|list|open|reschedule|rename|update)\b")  # M2.3b fix round
UPDATE_CUE = re.compile(r"\b(anymore|any more|no longer|moved to|(chhod|chod) (di|diya|dia))\b"
                        r"|\bab\b.*\bnahi\b")
# M2.3b fix round, rule A (approved): a message made only of these words (and
# first-person words) is small talk, never a memory. Chosen after reading the
# fix-round set's small-talk lines, so S01-S06 are not blind to it.
SMALL_TALK = {
    "hoon", "hu", "hai", "hain", "raha", "rahi", "aa", "ja", "so", "just", "also", "bhi",
    "bilkul", "well", "ok", "okay", "theek", "thik", "fine", "good", "great", "sahi", "accha",
    "haan", "yes", "yeah", "no", "nahi", "sure", "cool", "sorry", "alright", "right",
    "thanks", "thank", "you", "shukriya", "agree", "think", "see", "checking", "pata"}


# The message's words in lower case, apostrophes kept ("i'm", "don't").
def words_of(text: str) -> list[str]:
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower().replace("’", "'"))


# True when the message is a question: it ends in "?", starts with an English
# question word (not "is", which needs the "?"), or holds a Hinglish question word ("kya", "kab", ...) anywhere.
def is_question(text: str) -> bool:
    words = words_of(text)
    if text.strip().endswith("?") or not words:
        return True
    return words[0] in QUESTION_START or any(w in HINGLISH_QUESTION for w in words)


# True when the message says "remember" / "yaad rakhna" at its start or end.
def says_remember(text: str) -> bool:
    return bool(REMEMBER.search(text) or REMEMBER_AT_END.search(text))


# True when the message has a first-person word (I, my, main, mera, mujhe, ...).
def first_person(text: str) -> bool:
    return any(w in FIRST_PERSON for w in words_of(text))


# True when the message asks Leo to do something (remind, batao, set, cancel, ...).
def is_request(text: str) -> bool:
    return bool(REQUEST.search(" ".join(words_of(text))))


# True when the message may be a lasting fact: never a question; yes for
# "remember" words or a first-person statement that is not a request or small talk.
def worth_remembering(text: str) -> bool:
    if is_question(text):
        return False
    return says_remember(text) or (first_person(text) and not is_request(text)
                                   and not is_small_talk(text))


# True when every word is a first-person or small-talk word ("I'm fine, thanks").
def is_small_talk(text: str) -> bool:
    return all(w in FIRST_PERSON or w in SMALL_TALK for w in words_of(text))


# True when the message says an older fact changed ("anymore", "chhod diya", ...).
def has_update_cue(text: str) -> bool:
    return bool(UPDATE_CUE.search(" ".join(words_of(text))))


# True when the message is a question about the user: the recall gate.
def is_personal_question(text: str) -> bool:
    return is_question(text) and first_person(text)


# The fact in the user's own words: the message without its "remember" words.
def fact_text(text: str) -> str:
    return REMEMBER_AT_END.sub("", REMEMBER.sub("", text, count=1)).strip()
