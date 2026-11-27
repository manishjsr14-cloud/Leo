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
    assert update == {"agent_queue": ["research"], "plan": ["get the weather"], "hops": 0,
                      "turn_kind": "question"}


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
    assert supervisor_node(STATE, chat, AGENTS) == {"agent_queue": [], "hops": 0,
                                                  "turn_kind": "question"}


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
    assert supervisor_node(STATE, chat, AGENTS) == {"agent_queue": [], "hops": 0,
                                                  "turn_kind": "question"}


# With no agents registered the supervisor makes no LLM call.
def test_no_agents_makes_no_llm_call():
    chat = FakeChat({"agents": ["research"], "task": "x"})
    assert supervisor_node(STATE, chat, []) == {"agent_queue": [], "hops": 0,
                                                  "turn_kind": "question"}
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


# Calendar example lines appear only when the calendar agent is on offer.
def test_calendar_examples_only_with_calendar():
    from leo.graph.supervisor import describe_agents
    assert "Mera Wednesday" not in describe_agents(["productivity", "research"])
    assert "Sabzi lena" not in describe_agents(["research", "calendar"])
    text = describe_agents(["research", "calendar"])
    assert '- "Mera Wednesday ka schedule batao" -> ["calendar"]' in text


# M1 exit check (K07): "what is on my calendar then?" goes to calendar by code, no LLM call.
def test_calendar_queries_are_planned_by_code():
    for text in ("Aaj shaam 5 baje kya hai?", "Saturday ko kya kya hai?", "What's on Saturday?",
                 "What do I have tomorrow at 5 pm?", "What's on my calendar on Thursday?",
                 "Kal subah 10:30 kya hai?"):
        chat = FakeChat({"agents": ["research"], "task": "x"})
        state = {"messages": [HumanMessage(text)], "hops": 0, "plan": []}
        update = supervisor_node(state, chat, ["research", "calendar"])
        assert update["agent_queue"] == ["calendar"] and chat.calls == [], text


# Other questions, and any question when calendar is not on offer, still go to the LLM.
def test_other_questions_still_go_to_the_llm():
    for text in ("Kal Pune mein mausam kya hai?", "What is 15% of 3200?", "Aaj kya date hai?",
                 "15 ka 20% kya hai?", "What's on Netflix tonight?", "kya hai?",
                 "Saturday subah khaali hai?"):
        chat = FakeChat({"agents": ["research"], "task": "x"})
        state = {"messages": [HumanMessage(text)], "hops": 0, "plan": []}
        supervisor_node(state, chat, ["research", "calendar", "productivity"])
        assert len(chat.calls) == 1, text
    chat = FakeChat({"agents": ["research"], "task": "x"})
    state = {"messages": [HumanMessage("Aaj shaam 5 baje kya hai?")], "hops": 0, "plan": []}
    supervisor_node(state, chat, ["research", "productivity"])
    assert len(chat.calls) == 1
