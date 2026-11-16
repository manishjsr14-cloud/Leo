"""Tests for M1.7's step changes in leo/agents/loop.py: the tool name is the
reply's only key, and an argument error is sent back to the model once."""

from langchain_core.messages import HumanMessage
from pydantic import ValidationError

from leo.agents.loop import run_steps
from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.registry import by_name
from tests.graph_fakes import llm_result

T10, T11 = "2026-11-19T16:30:00+05:30", "2026-11-19T17:30:00+05:30"
SAME = f'{{"create_event": {{"title": "Dentist", "start": "{T10}", "end": "{T10}"}}}}'
GOOD = f'{{"create_event": {{"title": "Dentist", "start": "{T10}", "end": "{T11}"}}}}'
DONE = '{"done": {"summary": "ok"}}'


class TextChat:
    """A fake LLM that returns planned raw texts, checked against the schema."""

    def __init__(self, *texts):
        self.texts, self.calls = list(texts), []

    # Return the next text, valid only when it matches the step schema.
    def __call__(self, messages, output_model=None, force_cloud=False):
        self.calls.append([dict(m) for m in messages])
        text = self.texts.pop(0)
        try:
            return llm_result(text, output_model.model_validate_json(text))
        except ValidationError:
            return llm_result(text, valid=False)


# Run the loop on the mock calendar with no extra prompt.
def run(chat):
    log = []
    tools = by_name(mock_calendar_tools(log))
    state = {"messages": [HumanMessage("add a dentist visit")], "agent_results": {}}
    return run_steps("prompt", "v", state, chat, tools, 6), log


# An end equal to its start fails the schema; the model sees the error once and fixes it.
def test_argument_error_is_sent_back_once():
    chat = TextChat(SAME, GOOD, DONE)
    out, log = run(chat)
    assert out["stopped"] == "done"
    assert out["steps"][0]["result"]["error"].startswith("bad arguments")
    assert [c.tool for c in log] == ["create_event"]
    assert "bad arguments" in chat.calls[1][-1]["content"]


# A second reply that fails the schema ends the run.
def test_second_argument_error_ends_the_run():
    out, log = run(TextChat(SAME, SAME))
    assert out["stopped"] == "invalid_output" and len(out["steps"]) == 1 and log == []


# A reply that names no known tool is not retried.
def test_unknown_shape_is_not_retried():
    out, _ = run(TextChat('{"tool": "create_event", "args": {}}'))
    assert out == {"steps": [], "summary": "", "stopped": "invalid_output"}
