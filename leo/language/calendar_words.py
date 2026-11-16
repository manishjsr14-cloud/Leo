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
