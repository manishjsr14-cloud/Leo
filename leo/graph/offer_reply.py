"""The code-written reply to a statement that names a coming event (M2.3c fix round a).

After a plain statement no agent runs and nothing is added (M2.3c). When the
statement names an event and a time (leo/language/event_offer.py), the reply
is written here, with no LLM call:
  - the parser read a date: an offer that shows it, with the time or the part
    of the day if given, in the user's language (prompts/replies.yaml,
    calendar_offer): "Mon 30 Nov, morning: should I add this to your calendar?"
  - the parser asks ("kal" with no tense): the parser's question (Hinglish only).
Otherwise None, and the responder's model answers as before.
"""

from datetime import datetime

from leo.graph.state import LeoState, latest_user_text
from leo.language.event_offer import event_time, part_of_day
from leo.language.say_time import say_clock, say_day
from leo.llm.prompts import load_prompt


# "Sun 29 Nov", "Sun 29 Nov, 4:00 pm" or "Mon 30 Nov, morning" (part named in `templates`).
def offer_when(text: str, parsed, templates: dict) -> str:
    when = say_day(parsed.date)
    if parsed.time is not None:
        return f"{when}, {say_clock(parsed.time)}"
    part = part_of_day(text)
    return f"{when}, {templates['part_' + part]}" if part else when


# The offer or the parser's question after a statement, or None.
def offer_reply(state: LeoState, now: datetime) -> str | None:
    if state.get("turn_kind") != "statement":
        return None
    text = latest_user_text(state)
    parsed = event_time(text, now)
    if parsed is None:
        return None
    if parsed.status == "ask":
        return parsed.question
    language = state.get("language")
    if language not in ("en", "hinglish"):
        return None
    templates = load_prompt("replies").extra(language)
    return templates["calendar_offer"].format(when=offer_when(text, parsed, templates))
