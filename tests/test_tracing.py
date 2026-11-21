"""Tracing through a whole request, with the fake tracer and fake LLM clients.

The real gateway runs (so LLM spans are real code) against a fake
OpenAI-style client; tools are the mocks. Nothing is sent anywhere.
"""

import json

import pytest

from leo import cli
from leo.agents.productivity import productivity_agent
from leo.graph.builder import build_graph
from leo.llm import gateway
from leo.ops import tracing
from leo.tools.mock.productivity import mock_productivity_tools
from leo.tools.registry import by_name, call_tool
from tests.llm_fakes import FakeClient, connection_error
from tests.tracing_fakes import FakeTracer

QUESTION = "what is 18% of 2450"
REPLY = "18% of 2450 = 441."
# Planned local-model replies: supervisor, agent step 1. Since M1.8 a single
# successful calculation ends the agent run and gets a code-written reply, so
# there is no "done" step and no responder LLM call.
PLAN = [
    json.dumps({"agents": ["productivity"], "task": "calculate 18% of 2450"}),
    json.dumps({"calculate": {"expression": "18% of 2450"}}),
]
# Text that must never reach a span when include_text is off.
FORBIDDEN = [QUESTION, "18% of 2450", "(18/100)", "is 441", '"441"', "You are", "calculate 18%"]


# Run one traced request through the real graph, gateway and mock tools.
def traced_run(include_text: bool) -> FakeTracer:
    tracer = FakeTracer()
    tracing.set_tracer(tracer, include_text)
    client = FakeClient(*PLAN)

    # The real gateway, on the fake local client.
    def chat(messages, output_model=None, force_cloud=False):
        return gateway.chat(messages, output_model, force_cloud, local_client=client)

    agent = productivity_agent(chat, by_name(mock_productivity_tools([])), max_steps=4)
    graph = build_graph(chat, agents={"productivity": agent})
    reply, _ = cli.run_turn(graph, [], QUESTION, False, session_id="session-1")
    assert reply.content == REPLY
    return tracer


def test_one_trace_with_nodes_steps_llm_and_tool_spans():
    tracer = traced_run(include_text=False)
    llm = ("llm:ollama", [])
    assert tracer.tree() == [("chat", [
        ("supervisor", [llm]),
        ("productivity", [
            ("step 1", [llm, ("tool:calculate", [])]),
        ]),
        ("responder", []),
    ])]
    kinds = {s["name"]: s["kind"] for s in tracer.spans}
    assert kinds == {"chat": "chain", "supervisor": "chain", "productivity": "agent",
                     "step 1": "span", "tool:calculate": "tool",
                     "llm:ollama": "generation", "responder": "chain"}


def test_without_include_text_no_text_reaches_any_span():
    tracer = traced_run(include_text=False)
    everything = json.dumps(tracer.spans, default=str)
    for text in FORBIDDEN:
        assert text not in everything, text
    assert all("input" not in s["fields"] and "output" not in s["fields"] for s in tracer.spans)


def test_with_include_text_inputs_and_outputs_are_recorded():
    tracer = traced_run(include_text=True)
    tool = tracer.named("tool:calculate")["fields"]
    assert tool["input"] == {"expression": "18% of 2450"}
    assert tool["output"]["result"] == "441"
    assert tracer.named("llm:ollama")["fields"]["input"]  # LLM text is recorded


def test_trace_tags_models_prompt_versions_and_tokens():
    tracer = traced_run(include_text=False)
    root = tracer.named("chat")["fields"]
    assert root["session_id"] == "session-1"
    assert "model:leo-qwen3" in root["tags"]
    assert any(t.startswith("prompt:supervisor@") for t in root["tags"])
    assert tracer.named("supervisor")["fields"]["metadata"]["prompt_version"] == "supervisor@2"
    assert tracer.named("supervisor")["fields"]["metadata"]["plan"] == ["productivity"]
    assert tracer.named("step 1")["fields"]["metadata"]["action"] == "calculate"
    llm = tracer.named("llm:ollama")["fields"]
    assert llm["model"] == "leo-qwen3"
    assert llm["usage_details"] == {"input": 10, "output": 5}
    assert llm["metadata"]["provider"] == "ollama" and llm["metadata"]["valid"] is True


def test_fallback_gives_two_llm_spans():
    tracer = FakeTracer()
    tracing.set_tracer(tracer)
    result = gateway.chat([{"role": "user", "content": "hi"}],
                          local_client=FakeClient(connection_error()),
                          cloud_client=FakeClient("hello"))
    assert result.provider == "groq"
    local, cloud = tracer.spans
    assert (local["name"], cloud["name"]) == ("llm:ollama", "llm:groq")
    assert local["fields"]["level"] == "ERROR"
    assert local["fields"]["status_message"] == "connection_error"
    assert cloud["fields"]["model"] == "openai/gpt-oss-120b"


def test_tool_error_span_records_only_the_error_type():
    tracer = FakeTracer()
    tracing.set_tracer(tracer)
    with pytest.raises(Exception, match="no task with id 99"):
        call_tool(by_name(mock_productivity_tools([])), "complete_task", {"task_id": 99})
    (span,) = tracer.spans
    assert span["name"] == "tool:complete_task" and span["error"] == "ToolError"
    assert "no task" not in json.dumps(span)
