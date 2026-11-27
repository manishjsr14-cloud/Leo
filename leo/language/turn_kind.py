"""What kind of message the user sent: a request, a question or a statement (M2.3c).

The user's rule (M2.3c), applied by the supervisor and the agents in code:
- statement (no request word and not a question): no agent runs and no tool
  is called; the reply may offer to add something, never add it;
- question: agents may run, but only read tools are offered;
- request: unchanged.

Request: the message holds a word of the existing memory REQUEST list
(leo/language/memory_words.py), or one of the few extra words below. The
extra words are kept out of that list on purpose, so what memory stores does
not change ("I start work at 9" stays a memory). A request wins over a
question: "Can you add milk?" is a request.
Question: the existing memory_words.is_question ("?" at the end, an English
question word first, or a Hinglish one anywhere).
Everything else is a statement ("Kal Rahul ke saath meeting" included).
M2.3c fix round b (the user's): a request word directly after a first-person
subject does not count ("I set my alarm early", "main delete kar deta hoon"),
so "Can I add milk?" is a question (known limit); "Can you add milk?" is not.
"""

import re

from leo.language.memory_words import REQUEST, is_question, words_of

# Approved for M2.3c: "start a timer", "alarm laga", "rakh do", "move it",
# "note likh lo" (M1.8 L19).
EXTRA_REQUEST = re.compile(r"\b(start|laga|rakh|rakho|move|likh|likho)\b")

SUBJECTS = {"i", "main", "maine", "hum", "we"}  # fix round b

REQUEST_KIND, QUESTION_KIND, STATEMENT_KIND = "request", "question", "statement"


# True when a request word in the message is not directly after a first-person
# subject ("I set ..." does not count; "Set ..." and "you add" do).
def has_request_word(joined: str) -> bool:
    for pattern in (REQUEST, EXTRA_REQUEST):
        for match in pattern.finditer(joined):
            before = joined[:match.start()].split()
            if not before or before[-1] not in SUBJECTS:
                return True
    return False


# The kind of the message: "request", "question" or "statement".
def turn_kind(text: str) -> str:
    if has_request_word(" ".join(words_of(text))):
        return REQUEST_KIND
    return QUESTION_KIND if is_question(text) else STATEMENT_KIND
