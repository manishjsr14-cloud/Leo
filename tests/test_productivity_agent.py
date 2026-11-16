"""Tests for leo/agents/productivity.py with a fake LLM and mock tools."""

import json

from langchain_core.messages import HumanMessage

from leo import cli
from leo.agents.productivity import productivity_agent, run_agent, run_tool, step_model
from leo.graph.builder import build_graph
from leo.graph.supervisor import SupervisorPlan
from leo.tools.mock.productivity import mock_productivity_tools
from leo.tools.registry import by_name
from tests.graph_fakes import FakeChat


# A fresh call log and the mock productivity tools that write to it.
def fresh():
    log = []
    return log, by_name(mock_productivity_tools(log))


# State for one user message, as the supervisor leaves it.
def state_for(text: str, task: str) -> dict:
    return {"messages": [HumanMessage(text)], "plan": [task], "agent_results": {}}


def test_add_milk_calls_add_task():
    log, tools = fresh()
    chat = FakeChat({"add_task": {"title": "milk"}},
                    {"done": {"summary": "Added milk."}})
    out = run_agent(state_for("add milk to my tasks", "add milk"), chat, tools, 4)
    assert [(c.tool, c.args) for c in log] == [("add_task", {"title": "milk"})]
    assert out["stopped"] == "done"
    assert out["steps"][0]["result"]["title"] == "milk"
    # The second LLM call saw the tool result.
    assert "Result of add_task" in chat.calls[1]["messages"][-1]["content"]


# The number comes from sympy: the fake LLM only copies the expression.
def test_percentage_is_computed_by_sympy_not_llm():
    log, tools = fresh()
    chat = FakeChat({"calculate": {"expression": "18% of 2450"}},
                    {"done": {"summary": "18% of 2450 is 441."}})
    out = run_agent(state_for("what is 18% of 2450", "calculate"), chat, tools, 4)
    assert log[0].result["result"] == "441"
    assert out["steps"][0]["result"]["computed"] == "(18/100)*2450"


def test_two_step_request_runs_inside_the_agent():
    log, tools = fresh()
    chat = FakeChat({"list_tasks": {}},
                    {"complete_task": {"task_id": 1}},
                    {"done": {"summary": "Marked Buy milk as done."}})
    out = run_agent(state_for("complete my milk task", "complete milk"), chat, tools, 4)
    assert [c.tool for c in log] == ["list_tasks", "complete_task"]
    assert log[1].args == {"task_id": 1}
    assert out["stopped"] == "done" and len(chat.calls) == 3


def test_step_limit_stops_a_loop():
    log, tools = fresh()
    chat = FakeChat(*[{"list_notes": {"limit": n}} for n in range(1, 6)])
    out = run_agent(state_for("notes?", "list"), chat, tools, 4)  # never says done
    assert len(chat.calls) == 4 and len(log) == 4
    assert out["stopped"] == "max_steps"


def test_tool_errors_go_back_to_the_model():
    log, tools = fresh()
    chat = FakeChat({"complete_task": {"task_id": 99}},
                    {"done": {"summary": "Could not."}})
    out = run_agent(state_for("complete task 99", "complete"), chat, tools, 4)
    error = {"error": "no task with id 99; use list_tasks for ids"}
    assert out["steps"][0]["result"] == error
    assert json.dumps(error) in chat.calls[1]["messages"][-1]["content"]
    assert [c.tool for c in log] == ["complete_task"]


# run_tool turns bad arguments and unknown tools into errors, never exceptions.
def test_run_tool_returns_errors_instead_of_raising():
    log, tools = fresh()
    bad = run_tool(tools, "add_task", {"title": "x", "priority": 1})
    assert bad["error"].startswith("bad arguments: priority")
    assert "no tool named" in run_tool(tools, "delete_everything", {})["error"]
    assert log == []


def test_invalid_llm_output_stops_without_running_tools():
    log, tools = fresh()
    out = run_agent(state_for("hi", "x"), FakeChat(None), tools, 4)
    assert out == {"steps": [], "summary": "", "stopped": "invalid_output"}
    assert log == []


# The schema allows only real tools, each with its own required arguments.
def test_step_schema_requires_real_tools_and_their_args():
    _, tools = fresh()
    schema = step_model(tools)
    for bad in ['{"delete_everything": {}}',
                '{"tool": "add_task"}',  # the first real run's failure: no args
                '{"add_task": {}}',
                '{"add_task": {"title": "milk", "approved": true}}',
                '{"args": {}}',
                # the old M1.4 shape is no longer accepted (changed in M1.7)
                '{"tool": "add_task", "args": {"title": "milk"}}',
                '{"done": true, "summary": "ok"}',
                # one key per reply: a tool and done together is refused
                '{"add_task": {"title": "milk"}, "done": {"summary": "x"}}']:
        assert not _valid(schema, bad), bad
    assert _valid(schema, '{"add_task": {"title": "milk"}}')
    assert _valid(schema, '{"done": {"summary": "ok"}}')


# The first step must be a tool call; done is offered only on later steps,
# and "cannot" is never offered.
def test_first_step_must_be_a_tool_call():
    _, tools = fresh()
    first, later = step_model(tools, first_step=True), step_model(tools)
    assert not _valid(first, '{"done": {"summary": "Added milk."}}')
    assert _valid(first, '{"calculate": {"expression": "2+2"}}')
    assert _valid(later, '{"done": {"summary": "ok"}}')
    for schema in (first, later):
        assert not _valid(schema, '{"cannot": {"reason": "not my job"}}')


# Only an agent that returned done goes into completed_agents.
def test_completed_agents_only_after_done():
    _, tools = fresh()
    done = productivity_agent(FakeChat({"list_tasks": {}},
                                       {"done": {"summary": "ok"}}), tools, 4)
    looping = productivity_agent(FakeChat({"list_tasks": {}}), tools, 2)
    assert done(state_for("tasks?", "list"), {})["completed_agents"] == ["productivity"]
    assert "completed_agents" not in looping(state_for("tasks?", "list"), {})


# True when `text` passes the schema.
def _valid(schema, text: str) -> bool:
    try:
        schema.model_validate_json(text)
        return True
    except ValueError:
        return False


# Whole graph: one supervisor call plans [productivity], the agent runs two
# tools and says done, the graph goes on to the responder with no second
# supervisor call, and the responder sees the agent's results.
def test_graph_two_step_needs_no_extra_supervisor_call():
    log, tools = fresh()
    chat = FakeChat(
        {"agents": ["productivity"], "task": "complete the milk task"},
        {"list_tasks": {}},
        {"complete_task": {"task_id": 1}},
        {"done": {"summary": "Marked Buy milk as done."}},
        "Done, Buy milk is ticked off.",
    )
    agent = productivity_agent(chat, tools, max_steps=4)
    out = build_graph(chat, agents={"productivity": agent}).invoke(
        {"messages": [HumanMessage("complete my milk task")], "hops": 0, "plan": []})
    supervisor_calls = [c for c in chat.calls if _is_supervisor(c)]
    assert len(supervisor_calls) == 1 and out["hops"] == 1
    assert out["completed_agents"] == ["productivity"]
    assert [c.tool for c in log] == ["list_tasks", "complete_task"]
    responder_sees = " ".join(m["content"] for m in chat.calls[-1]["messages"])
    assert 'complete_task({"task_id": 1}) -> {"id": 1, "title": "Buy milk", "done": true}'         in responder_sees
    assert "Marked Buy milk as done." not in responder_sees  # LLM summary is not passed on
    assert out["messages"][-1].content == "Done, Buy milk is ticked off."


# True when a recorded fake LLM call came from the supervisor.
def _is_supervisor(call) -> bool:
    model = call["output_model"]
    return isinstance(model, type) and issubclass(model, SupervisorPlan)


# Two requests through the CLI's run_turn: each runs the tool exactly once,
# and completed_agents starts empty again for the second request.
def test_tools_run_once_per_request_across_turns():
    log, tools = fresh()
    route = {"agents": ["productivity"], "task": "add the task"}
    chat = FakeChat(
        route, {"add_task": {"title": "milk"}},
        {"done": {"summary": "Added milk."}}, "Added milk.",
        route, {"add_task": {"title": "eggs"}},
        {"done": {"summary": "Added eggs."}}, "Added eggs.",
    )
    graph = build_graph(chat, agents={"productivity": productivity_agent(chat, tools, 4)})
    _, history = cli.run_turn(graph, [], "add milk to my tasks", False)
    reply, _ = cli.run_turn(graph, history, "add eggs to my tasks", False)
    assert [(c.tool, c.args["title"]) for c in log] == [("add_task", "milk"), ("add_task", "eggs")]
    assert sum(_is_supervisor(c) for c in chat.calls) == 2
    assert reply.content == "Added eggs."
