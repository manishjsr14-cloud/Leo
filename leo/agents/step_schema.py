"""The shape of one agent step reply (section 4.2, decision M1.4; shape changed in M1.7).

Each option is an object with ONE key, the tool name, holding that tool's
arguments:  {"create_event": {"title": ..., "start": ..., "end": ...}}
and finishing is  {"done": {"summary": "..."}}.
Ollama writes object keys in alphabetical order, so with the old shape
{"tool": ..., "args": ...} the model wrote "args" first and had to pick the
arguments before the tool (first M1.7 report: invented cancel_event ids). With
the tool name as the key, the first thing the model writes is the tool choice.
"""

import json
from typing import Any, Union

from pydantic import BaseModel, ConfigDict, RootModel, create_model

from leo.tools.base import Tool


class DoneSummary(BaseModel):
    """What a finished agent hands back: a short summary for the responder."""

    model_config = ConfigDict(extra="forbid")

    summary: str


class Done(BaseModel):
    """The reply that ends the loop: {"done": {"summary": "..."}}."""

    model_config = ConfigDict(extra="forbid")

    done: DoneSummary


# The step schema for these tools: one option per tool, each with that tool's
# own required, typed arguments. Ollama's structured output then cannot invent a
# tool or leave out its arguments (see the first M1.4 report).
# The first step leaves Done out: the model said "done" without calling any
# tool, so it must act first. (A "cannot" option was tried and dropped: the
# model declined requests it could do; see the third M1.4 report.)
def step_model(tools: dict[str, Tool], first_step: bool = False) -> type[RootModel]:
    options: list[type[BaseModel]] = [
        create_model(f"Call_{name}", __config__=ConfigDict(extra="forbid"),
                     **{name: (tool.args_model, ...)})
        for name, tool in tools.items()
    ]
    if not first_step:
        options.append(Done)
    return RootModel[Union[tuple(options)]]  # noqa: UP007


# The (key, value) of a parsed step: ("create_event", <args>) or ("done", <summary>).
def read_action(action: BaseModel) -> tuple[str, Any]:
    name = next(iter(type(action).model_fields))
    return name, getattr(action, name)


# For a reply that failed the schema: (tool name, raw arguments) when it still
# names one known tool with an object of arguments, else None.
def loose_call(text: str, tools: dict[str, Tool]) -> tuple[str, dict] | None:
    try:
        data = json.loads(text)
    except ValueError:
        return None
    if isinstance(data, dict) and len(data) == 1:
        name, args = next(iter(data.items()))
        if name in tools and isinstance(args, dict):
            return name, args
    return None
