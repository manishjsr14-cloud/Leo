"""Words that decide which calendar tools the model is offered (M1.7 run2).

The local model fills the step schema "args" first (Ollama writes keys in
alphabetical order), so with cancel_event on offer it often began
{"args": {"event_id": ...}} and invented an id (first M1.7 report). Code now
offers cancel_event only when the user asked to cancel, and move_event only
when the user asked to move (or two times were found).
"""

from leo.language.time_parser import split_words

# Words (and two-word phrases) that ask to cancel. Lowercase Roman spellings.
CANCEL_WORDS = {"cancel", "hatao", "clear", "delete", "remove"}
CANCEL_PHRASES = {"hata do"}

# Words that ask to move an event.
MOVE_WORDS = {"move", "shift", "badal", "change"}


# True when the text asks to cancel something.
def asks_to_cancel(text: str) -> bool:
    words = split_words(text)
    joined = " ".join(words)
    return bool(set(words) & CANCEL_WORDS) or any(p in joined for p in CANCEL_PHRASES)


# True when the text asks to move something.
def asks_to_move(text: str) -> bool:
    return bool(set(split_words(text)) & MOVE_WORDS)


# Words that ask to add an event. With two times in the message as well, the
# agent asks instead of guessing between "add 3 to 5" and "move 3 to 5".
CREATE_WORDS = {"add", "daal", "rakh", "laga", "schedule", "plan", "book"}
ADD_OR_MOVE = ("Message mein do time hain. Nayi event banani hai (kis time se kis time "
               "tak?) ya koi meeting ek time se doosre time pe move karni hai?")


# True when the text asks to add an event.
def asks_to_create(text: str) -> bool:
    return bool(set(split_words(text)) & CREATE_WORDS)
