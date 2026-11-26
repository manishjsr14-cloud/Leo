"""Every field in a structured reply is required (architecture section 6.6, M2.3b fix
round): walks every schema Leo sends to the model as structured output."""

from leo.agents.step_schema import step_model
from leo.graph.memory_nodes import MemoryDecision
from leo.graph.supervisor import plan_model
from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.mock.productivity import mock_productivity_tools
from leo.tools.mock.research import mock_research_tools
from leo.tools.registry import by_name

# Found by the M2.3b fix-round audit, left for the user to decide (tool arguments
# the agents fill in). Remove a line once its field is required.
KNOWN_OPTIONAL = {"WebSearchArgs.max_results", "ListTasksArgs.include_done",
                  "CompleteTaskArgs.task_id", "CompleteTaskArgs.title",
                  "ListNotesArgs.limit", "StartTimerArgs.label"}


# "Model.field" for every property that is not required or has a default.
def optional_fields(schema: dict) -> set[str]:
    found, defs = set(), schema.get("$defs", {})
    for name, part in [(schema.get("title", "root"), schema), *defs.items()]:
        required = set(part.get("required", []))
        for prop, sub in part.get("properties", {}).items():
            if prop not in required or "default" in sub:
                found.add(f"{name}.{prop}")
    return found


# The memory extraction reply and the supervisor plan have no optional field.
def test_memory_and_supervisor_replies_are_all_required():
    assert optional_fields(MemoryDecision.model_json_schema()) == set()
    assert optional_fields(plan_model(["calendar", "research"]).model_json_schema()) == set()


# Agent step replies: no optional field beyond the known list.
def test_agent_step_replies_have_no_new_optional_field():
    found = set()
    for tools in (mock_calendar_tools([], []), mock_research_tools([], []),
                  mock_productivity_tools([])):
        found |= optional_fields(step_model(by_name(tools)).model_json_schema())
    assert found == KNOWN_OPTIONAL
