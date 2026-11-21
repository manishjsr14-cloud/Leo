"""When an agent may finish without asking the LLM again (M1.8, speed).

After one successful tool call the model used to spend a whole LLM call just
to say "done". The step loop now ends the run in code (stopped "done", the
summary written by code) right after a step when this agent's rule says so:
  - the message links no other request (no "aur", "and", "agar", comma, ...;
    leo/language/normalize.has_joiner), and
  - the tool is one that ends a run for this agent (a single write such as
    create_event or add_task; never cancel_event, since "clear" may mean
    several), or it is a read and the message asks for no change.
Anything else (multi-step requests such as M1.7 t10, a move that needs
get_events first) goes back to the model as before.
"""

from collections.abc import Callable

from leo.language.normalize import has_joiner

Finish = Callable[[str], bool]


# The rule for one message: given the tool that just succeeded (or was refused
# for approval), True to finish now. None when the message links requests.
def finish_rule(text: str, ends_run: set[str], reads: set[str] = frozenset(),
                asks_change: bool = True) -> Finish | None:
    if has_joiner(text):
        return None

    # True when this tool's result is the answer to the message.
    def finish(tool: str) -> bool:
        return tool in ends_run or (tool in reads and not asks_change)

    return finish
