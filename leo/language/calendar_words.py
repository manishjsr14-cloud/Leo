"""Words that decide which calendar tools the model is offered (M1.7 run2).

The local model fills the step schema "args" first (Ollama writes keys in
alphabetical order), so with cancel_event on offer it often began
{"args": {"event_id": ...}} and invented an id (first M1.7 report). Code now
offers cancel_event only when the user asked to cancel, and move_event only
when the user asked to move (or two times were found).
M1 exit check: only a command ("clear kar do", "clear my ...") is a clear;
"Saturday subah khaali hai?" and "Is my Saturday morning clear?" ask about
free time, so they never offer cancel_event.
"""

from leo.language.time_parser import split_words

# Words (and two-word phrases) that ask to cancel. Lowercase Roman spellings.
CANCEL_WORDS = {"cancel", "hatao", "delete", "remove"}
CANCEL_PHRASES = {"hata do"}
# Commands that clear a range (every event in it); questions are not clears.
CLEAR_PHRASES = {"clear kar do", "clear kardo", "clear karo", "clear kar dena", "clear my",
                 "clear out", "khaali kar do", "khali kar do", "khaali karo", "khali karo"}

# Words that ask to move an event.
MOVE_WORDS = {"move", "shift", "badal", "change"}


# True when the text holds one of these phrases as whole words.
def has_phrase(text: str, phrases: set[str]) -> bool:
    joined = f" {' '.join(split_words(text))} "
    return any(f" {p} " in joined for p in phrases)


# True when the text commands a clear ("Saturday subah clear kar do").
def asks_to_clear(text: str) -> bool:
    return has_phrase(text, CLEAR_PHRASES)


# True when the text asks to cancel something (a clear is a cancel too).
def asks_to_cancel(text: str) -> bool:
    return (bool(set(split_words(text)) & CANCEL_WORDS) or has_phrase(text, CANCEL_PHRASES)
            or asks_to_clear(text))


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
