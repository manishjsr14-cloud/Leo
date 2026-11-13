"""Tests for the supervisor and responder nodes, using a fake LLM."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import ValidationError

from leo.graph.responder import responder_node
from leo.graph.supervisor import (
    FINISH,
    SupervisorDecision,
    decision_model,
    supervisor_node,
)
from tests.graph_fakes import FakeChat

STATE = {"messages": [HumanMessage("what is the weather?")], "hops": 0, "plan": []}
AGENTS = ["research"]


# A valid choice of agent sets next_agent, records the task and counts a hop.
def test_valid_choice_routes_to_agent():
    chat = FakeChat({"next": "research", "task": "get the weather"})
    update = supervisor_node(STATE, chat, AGENTS, max_hops=8)
    assert update == {"next_agent": "research", "plan": ["get the weather"], "hops": 1}


# The LLM request asks for the SupervisorDecision schema and lists the agents.
def test_request_uses_schema_and_lists_agents():
    chat = FakeChat({"next": FINISH, "task": ""})
    supervisor_node(STATE, chat, AGENTS, max_hops=8)
    call = chat.calls[0]
    assert issubclass(call["output_model"], SupervisorDecision)
    assert "research" in call["messages"][0]["content"]
    assert call["messages"][-1] == {"role": "user", "content": "what is the weather?"}


# FINISH from the LLM finishes without counting a hop.
def test_finish_choice():
    chat = FakeChat({"next": FINISH, "task": "done"})
    assert supervisor_node(STATE, chat, AGENTS, max_hops=8) == {"next_agent": FINISH}


# The schema offers only the given agents and FINISH, so an unknown name is invalid.
def test_schema_offers_only_given_agents_and_finish():
    schema = decision_model(["research", "productivity"])
    assert schema.model_validate({"next": "research", "task": "x"}).next == "research"
    assert schema.model_validate({"next": FINISH, "task": ""}).next == FINISH
    with pytest.raises(ValidationError):
        schema.model_validate({"next": "astrology", "task": "read stars"})


# An agent that finished this request is left out of the schema and the prompt.
def test_completed_agent_is_not_offered_again():
    chat = FakeChat({"next": "research", "task": "x"})
    state = {**STATE, "completed_agents": ["productivity"]}
    supervisor_node(state, chat, ["productivity", "research"], max_hops=8)
    schema = chat.calls[0]["output_model"]
    with pytest.raises(ValidationError):
        schema.model_validate({"next": "productivity", "task": "again"})
    assert "productivity" not in chat.calls[0]["messages"][0]["content"]


# When every agent has finished this request, FINISH comes with no LLM call.
def test_all_agents_completed_finishes_without_llm_call():
    chat = FakeChat({"next": "research", "task": "again"})
    state = {**STATE, "completed_agents": ["research"]}
    assert supervisor_node(state, chat, AGENTS, max_hops=8) == {"next_agent": FINISH}
    assert chat.calls == []


# A reply that fails the schema finishes.
def test_invalid_reply_finishes():
    chat = FakeChat(None)
    assert supervisor_node(STATE, chat, AGENTS, max_hops=8) == {"next_agent": FINISH}


# At the hop limit the supervisor finishes without calling the LLM.
def test_hop_limit_finishes_without_llm_call():
    chat = FakeChat({"next": "research", "task": "again"})
    update = supervisor_node({**STATE, "hops": 8}, chat, AGENTS, max_hops=8)
    assert update == {"next_agent": FINISH}
    assert chat.calls == []


# With no agents registered the supervisor finishes without calling the LLM.
def test_no_agents_finishes_without_llm_call():
    chat = FakeChat({"next": "research", "task": "x"})
    assert supervisor_node(STATE, chat, [], max_hops=8) == {"next_agent": FINISH}
    assert chat.calls == []


# The supervisor passes force_cloud on to the gateway.
def test_supervisor_passes_force_cloud():
    chat = FakeChat({"next": FINISH, "task": ""})
    supervisor_node(STATE, chat, AGENTS, max_hops=8, force_cloud=True)
    assert chat.calls[0]["force_cloud"] is True


# The responder adds one AI message with the provider in its metadata,
# and includes agent results in what it sends to the LLM.
def test_responder_adds_reply_with_provider():
    chat = FakeChat("It will be sunny.")
    state = {**STATE, "agent_results": {"research": "sunny, 31 C"}}
    update = responder_node(state, chat, force_cloud=True)
    (reply,) = update["messages"]
    assert isinstance(reply, AIMessage)
    assert reply.content == "It will be sunny."
    assert reply.response_metadata["provider"] == "groq"
    sent = " ".join(m["content"] for m in chat.calls[0]["messages"])
    assert "sunny, 31 C" in sent
    assert chat.calls[0]["output_model"] is None
