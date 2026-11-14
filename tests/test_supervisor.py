"""Tests for the supervisor and responder nodes, using a fake LLM."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import ValidationError

from leo.graph.responder import responder_node
from leo.graph.supervisor import SupervisorPlan, plan_model, supervisor_node
from tests.graph_fakes import FakeChat

STATE = {"messages": [HumanMessage("what is the weather?")], "hops": 0, "plan": []}
AGENTS = ["productivity", "research"]


# A valid plan sets the agent queue, records the task and resets hops.
def test_valid_plan_sets_the_queue():
    chat = FakeChat({"agents": ["research"], "task": "get the weather"})
    update = supervisor_node(STATE, chat, AGENTS)
    assert update == {"agent_queue": ["research"], "plan": ["get the weather"], "hops": 0}


# The LLM request asks for the SupervisorPlan schema and lists the agents.
def test_request_uses_schema_and_lists_agents():
    chat = FakeChat({"agents": [], "task": ""})
    supervisor_node(STATE, chat, AGENTS)
    call = chat.calls[0]
    assert issubclass(call["output_model"], SupervisorPlan)
    assert "- research: web search, reading web pages, weather" in call["messages"][0]["content"]
    assert call["messages"][-1] == {"role": "user", "content": "what is the weather?"}


# An empty plan (plain chat) leaves the queue empty and adds no task.
def test_empty_plan_means_no_agents():
    chat = FakeChat({"agents": [], "task": ""})
    assert supervisor_node(STATE, chat, AGENTS) == {"agent_queue": [], "hops": 0}


# The schema allows only known names, no duplicates, and at most 2 agents.
def test_schema_limits_the_plan():
    schema = plan_model(AGENTS)
    ok = schema.model_validate({"agents": ["research", "productivity"], "task": "x"})
    assert ok.agents == ["research", "productivity"]
    for bad in [["astrology"], ["research", "research"],
                ["research", "productivity", "research"]]:
        with pytest.raises(ValidationError):
            schema.model_validate({"agents": bad, "task": "x"})


# A reply that fails the schema means no agents: the responder answers.
def test_invalid_reply_runs_no_agents():
    chat = FakeChat(None)
    assert supervisor_node(STATE, chat, AGENTS) == {"agent_queue": [], "hops": 0}


# With no agents registered the supervisor makes no LLM call.
def test_no_agents_makes_no_llm_call():
    chat = FakeChat({"agents": ["research"], "task": "x"})
    assert supervisor_node(STATE, chat, []) == {"agent_queue": [], "hops": 0}
    assert chat.calls == []


# The supervisor passes force_cloud on to the gateway.
def test_supervisor_passes_force_cloud():
    chat = FakeChat({"agents": [], "task": ""})
    supervisor_node(STATE, chat, AGENTS, force_cloud=True)
    assert chat.calls[0]["force_cloud"] is True


# The responder adds one AI message with the provider in its metadata,
# and includes agent results in what it sends to the LLM.
def test_responder_adds_reply_with_provider():
    chat = FakeChat("It will be sunny.")
    step = {"tool": "get_weather", "args": {}, "result": "sunny, 31 C"}
    state = {**STATE, "agent_results": {"research": {"steps": [step]}}}
    update = responder_node(state, chat, force_cloud=True)
    (reply,) = update["messages"]
    assert isinstance(reply, AIMessage)
    assert reply.content == "It will be sunny."
    assert reply.response_metadata["provider"] == "groq"
    sent = " ".join(m["content"] for m in chat.calls[0]["messages"])
    assert "sunny, 31 C" in sent
    assert chat.calls[0]["output_model"] is None
