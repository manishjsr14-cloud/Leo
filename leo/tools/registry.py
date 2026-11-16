"""Find tools by name and call them safely (architecture sections 9 and 12.3).

call_tool is the only way agents run a tool. It checks the arguments against
the tool's schema, runs the tool's own extra check if it has one, and
refuses a 🔴 tool unless Leo's own code passes
approved=True. The approval never comes from the model's tool-call arguments:
those are checked against a schema that forbids unknown keys like "approved".
The full action rails (rate limits, taint tracking) move to
leo/guardrails/action_rails.py in a later task. Every call is traced as a
"tool" span: name and tier always; arguments and result only with include_text.
"""

from typing import Any

from leo.ops import tracing
from leo.tools.base import Tier, Tool, ToolCall
from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.mock.productivity import mock_productivity_tools
from leo.tools.mock.research import mock_research_tools


class UnknownToolError(LookupError):
    """The model asked for a tool that does not exist."""


class ApprovalRequiredError(PermissionError):
    """A 🔴 tool was called without human approval."""


# Turn a list of tools into a name -> tool dict, refusing duplicate names.
def by_name(tools: list[Tool]) -> dict[str, Tool]:
    table: dict[str, Tool] = {}
    for tool in tools:
        if tool.name in table:
            raise ValueError(f"duplicate tool name: {tool.name}")
        table[tool.name] = tool
    return table


# All mock tools, keyed by name. Every call they make is appended to `log`.
def mock_tools(log: list[ToolCall]) -> dict[str, Tool]:
    return by_name(mock_calendar_tools(log) + mock_productivity_tools(log)
                   + mock_research_tools(log))


# Run one tool. `args` is what the model sent; `approved` is set only by Leo's
# own code (the human_approval step), never taken from `args`.
# Raises UnknownToolError, pydantic.ValidationError or ApprovalRequiredError.
def call_tool(
    tools: dict[str, Tool], name: str, args: dict[str, Any], *, approved: bool = False
) -> Any:
    tool = tools.get(name)
    tier = tool.tier.value if tool is not None else None
    with tracing.span(f"tool:{name}", "tool", input=tracing.text(args),
                      metadata={"tool": name, "tier": tier}) as span:
        if tool is None:
            raise UnknownToolError(f"no tool named {name!r}")
        checked = tool.args_model.model_validate(args)
        if tool.check is not None:
            tool.check(checked)  # e.g. the calendar guard; before approval is asked
        if tool.tier is Tier.CONFIRM and approved is not True:
            raise ApprovalRequiredError(f"{name} needs human approval")
        result = tool.fn(checked)
        span.update(output=tracing.text(result))
        return result
