"""A word rule that decides when a message may hold a fact worth remembering (M2.3).

Most turns are requests and questions, so memory_write must not add an LLM call
to every turn. This rule runs first, in code: only a message it picks goes to
the extraction step (one LLM call), which then decides "remember" or not and
gives the subject.

The word lists below were fixed in the M2.3 proposal, before the check set
(evals/scenarios/m2_3_memory_questions.yaml) was written, and were not changed
after seeing it:
  never:      questions ("?" or a question word)
  remember:   remember, yaad rakhna, yaad rakho, yaad rakh lo
  English:    I am / I'm, I eat / don't eat, I like / love / hate / prefer,
              I'm allergic, I live / work, my ... is, anymore
  Hinglish:   mera / meri / mere ... hai / hain, main ... hoon / hu,
              mujhe ... pasand hai / nahi, mujhe ... allergy hai, main ... nahi khata / khati
"note kar lo" is left out: it asks for the notes tool.
"""

import re

REMEMBER = re.compile(r"^\s*(yaad rakh lo|yaad rakhna|yaad rakho|remember that|remember)\b"
                      r"[\s,:;.!-]*", re.IGNORECASE)
REMEMBER_AT_END = re.compile(r"[\s,;-]*\b(yaad rakh lo|yaad rakhna|yaad rakho|remember that)"
                             r"\s*[.!]*\s*$", re.IGNORECASE)
QUESTION_START = {"what", "when", "where", "who", "which", "how", "why", "do", "does", "did",
                  "is", "am", "are", "can"}
HINGLISH_QUESTION = {"kya", "kab", "kahan", "kaun", "kaunsa", "kaunsi", "kitna", "kitne", "kitni",
                     "kaise", "kyun", "kyon"}
FACT_FORMS = [re.compile(p) for p in (
    r"\bi am\b", r"\bi'm\b", r"\bi (eat|like|love|hate|prefer|live|work)\b",
    r"\bi (don't|do not) eat\b", r"\bmy\b.+\bis\b", r"\banymore\b",
    r"\b(mera|meri|mere)\b.*\b(hai|hain)\b", r"\bmain\b.*\b(hoon|hu)\b",
    r"\bmujhe\b.*\bpasand\b.*\b(hai|hain|nahi)\b", r"\bmujhe\b.*\ballergy\b.*\bhai\b",
    r"\bmain\b.*\bnahi (khata|khati)\b")]


# The message's words in lower case, apostrophes kept ("i'm", "don't").
def words_of(text: str) -> list[str]:
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower().replace("’", "'"))


# True when the message is a question: it ends in "?", starts with an English
# question word, or holds a Hinglish question word ("kya", "kab", ...) anywhere.
def is_question(text: str) -> bool:
    words = words_of(text)
    if text.strip().endswith("?") or not words:
        return True
    return words[0] in QUESTION_START or any(w in HINGLISH_QUESTION for w in words)


# True when the message says "remember" / "yaad rakhna" at its start or end.
def says_remember(text: str) -> bool:
    return bool(REMEMBER.search(text) or REMEMBER_AT_END.search(text))


# True when the message may hold a lasting fact: never for a question; yes for
# "remember" words or a first-person fact form.
def worth_remembering(text: str) -> bool:
    if is_question(text):
        return False
    lowered = " ".join(words_of(text))
    return says_remember(text) or any(p.search(lowered) for p in FACT_FORMS)


# The fact in the user's own words: the message without its "remember" words.
def fact_text(text: str) -> str:
    return REMEMBER_AT_END.sub("", REMEMBER.sub("", text, count=1)).strip()
