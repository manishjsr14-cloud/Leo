"""Tests for the compiled graph in leo/graph/builder.py, using a fake LLM."""

from langchain_core.messages import AIMessage, HumanMessage

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


# Hop limit: an LLM that always picks the same agent is stopped after
# graph.max_hops (8) agent runs, then the responder answers.
def test_hop_limit_stops_loop():
    runs = []
    calls = []

    # A dummy agent that only counts how often it ran.
    def dummy(state):
        runs.append(state["plan"][-1])
        return {"agent_results": {"dummy": f"run {len(runs)}"}}

    # The supervisor always picks "dummy"; the responder gets plain text.
    def chat(messages, output_model=None, force_cloud=False):
        calls.append(output_model)
        decision = {"next": "dummy", "task": "loop forever"}
        return FakeChat(decision if output_model else "Stopped.")(
            messages, output_model, force_cloud)

    graph = build_graph(chat, agents={"dummy": dummy})
    out = graph.invoke({"messages": [HumanMessage("loop")], "hops": 0, "plan": []})
    assert len(runs) == 8
    assert out["hops"] == 8
    assert out["next_agent"] == "FINISH"
    assert out["messages"][-1].content == "Stopped."
    # 8 supervisor calls that chose dummy, then one responder call; the 9th
    # supervisor turn hits the limit and makes no call.
    assert len(calls) == 9
    assert calls[-1] is None
