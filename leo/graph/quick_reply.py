"""Replies written by code for one successful write, with no LLM call (M1.8).

When exactly one agent ran, it finished ("done") after exactly one step, and
that step was a successful write (create or move an event, add or complete a
task, add a note, start a timer, a calculation), the reply comes from the
templates in prompts/replies.yaml, in English or Hinglish by the language tag.
This saves the responder's LLM call and keeps the wording exact (M1.4 runs
said "already complete" after a task was completed). When the am/pm of the
event time was assumed ("4 baje" -> 4 pm), the reply asks about it.
Reads, questions, refusals, Hindi (Devanagari) messages and multi-step
requests still go to the LLM responder.
"""

from datetime import datetime

from leo.graph.state import LeoState
from leo.language.say_time import say_clock, say_iso_span
from leo.llm.prompts import load_prompt

WRITES = {"create_event", "move_event", "add_task", "complete_task", "add_note",
          "start_timer", "calculate"}
EVENT_WRITES = {"create_event", "move_event"}


# The template values for one tool result.
def template_values(tool: str, result: dict) -> dict:
    if tool in EVENT_WRITES:
        return {"title": result["title"], "when": say_iso_span(result["start"], result["end"])}
    if tool == "start_timer":
        minutes = float(result["minutes"])
        return {"label": result["label"],
                "minutes": int(minutes) if minutes.is_integer() else minutes}
    return dict(result)


# The single step of the only agent that ran, with its outcome, or None.
def single_step(state: LeoState) -> tuple[dict, dict] | None:
    results = state.get("agent_results") or {}
    if len(results) != 1:
        return None
    outcome = next(iter(results.values()))
    if not isinstance(outcome, dict) or outcome.get("stopped") != "done":
        return None
    steps = outcome.get("steps", [])
    return (steps[0], outcome) if len(steps) == 1 else None


# The code-written reply, or None when the LLM responder must answer.
def quick_reply(state: LeoState) -> str | None:
    language, found = state.get("language"), single_step(state)
    if language not in ("en", "hinglish") or found is None:
        return None
    step, outcome = found
    result = step.get("result")
    if step["tool"] not in WRITES or not isinstance(result, dict) or "error" in result:
        return None
    templates = load_prompt("replies").extra(language)
    try:
        text = templates[step["tool"]].format(**template_values(step["tool"], result))
        if outcome.get("assumed_ampm") and step["tool"] in EVENT_WRITES:
            clock = say_clock(datetime.fromisoformat(result["start"]))
            text += templates["assumed"].format(clock=clock)
    except (KeyError, TypeError, ValueError):
        return None
    return text
