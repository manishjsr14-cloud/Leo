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
"""

import re

from leo.language.memory_words import REQUEST, is_question, words_of

# Approved for M2.3c: "start a timer", "alarm laga", "rakh do", "move it",
# "note likh lo" (M1.8 L19).
EXTRA_REQUEST = re.compile(r"\b(start|laga|rakh|rakho|move|likh|likho)\b")

REQUEST_KIND, QUESTION_KIND, STATEMENT_KIND = "request", "question", "statement"


# The kind of the message: "request", "question" or "statement".
def turn_kind(text: str) -> str:
    joined = " ".join(words_of(text))
    if REQUEST.search(joined) or EXTRA_REQUEST.search(joined):
        return REQUEST_KIND
    return QUESTION_KIND if is_question(text) else STATEMENT_KIND
