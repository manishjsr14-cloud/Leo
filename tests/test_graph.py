"""Tests for the compiled graph in leo/graph/builder.py, using a fake LLM."""

from langchain_core.messages import AIMessage, HumanMessage

from leo.config import load_config
from leo.graph.builder import build_graph
from tests.graph_fakes import FakeChat


# A plain chat turn with no agents makes exactly one LLM call (the responder).
def test_plain_turn_makes_one_llm_call():
    chat = FakeChat("Hello! How can I help?")
    out = build_graph(chat).invoke({"messages": [HumanMessage("hi")]})
    assert len(chat.calls) == 1
    assert chat.calls[0]["output_model"] is None
    assert isinstance(out["messages"][-1], AIMessage)
    assert out["messages"][-1].content == "Hello! How can I help?"


# The responder sees the earlier turns of the conversation.
def test_responder_sees_history():
    chat = FakeChat("Your name is Asha.")
    history = [HumanMessage("my name is Asha"), AIMessage("Nice to meet you, Asha."),
               HumanMessage("what is my name?")]
    build_graph(chat).invoke({"messages": history})
    sent = [m["content"] for m in chat.calls[0]["messages"]]
    assert sent[-3:] == ["my name is Asha", "Nice to meet you, Asha.", "what is my name?"]


# force_cloud in the run config reaches the gateway call.
def test_force_cloud_reaches_gateway():
    chat = FakeChat("hi")
    build_graph(chat).invoke({"messages": [HumanMessage("hi")]},
                             {"configurable": {"force_cloud": True}})
    assert chat.calls[0]["force_cloud"] is True


# A dummy agent that records its name, the task, and the results it saw.
def dummy(name: str, seen: list):
    def run(state):
        seen.append((name, dict(state.get("agent_results") or {})))
        return {"agent_results": {**(state.get("agent_results") or {}), name: f"{name} ok"}}
    return run


# Run one request with this supervisor plan; returns (output, agent runs, LLM calls).
def run_plan(plan: list[str], config=None):
    seen: list = []
    chat = FakeChat({"agents": plan, "task": "do it"}, "Reply.")
    agents = {"productivity": dummy("productivity", seen), "research": dummy("research", seen)}
    out = build_graph(chat, agents=agents, config=config).invoke(
        {"messages": [HumanMessage("hi")], "hops": 0, "plan": []})
    return out, seen, chat.calls


def test_plan_of_productivity_never_runs_research():
    out, seen, calls = run_plan(["productivity"])
    assert [name for name, _ in seen] == ["productivity"]
    assert len(calls) == 2  # one supervisor plan, one responder; no second supervisor call
    assert out["messages"][-1].content == "Reply."


def test_plan_of_two_runs_both_in_order_and_second_sees_first():
    out, seen, calls = run_plan(["research", "productivity"])
    assert [name for name, _ in seen] == ["research", "productivity"]
    assert seen[1][1] == {"research": "research ok"}
    assert out["hops"] == 2 and len(calls) == 2


def test_empty_plan_goes_straight_to_the_responder():
    out, seen, calls = run_plan([])
    assert seen == [] and len(calls) == 2 and out["hops"] == 0


# max_hops stays a safety limit: with max_hops 1, only the first planned agent runs.
def test_max_hops_caps_the_planned_agents():
    config = load_config()
    config = config.model_copy(update={"graph": config.graph.model_copy(update={"max_hops": 1})})
    out, seen, _ = run_plan(["research", "productivity"], config)
    assert [name for name, _ in seen] == ["research"] and out["hops"] == 1
