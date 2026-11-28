"""M2.4 rolling summary (leo/graph/summary.py) with a fake LLM; no model, no leo_data/."""

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from leo import cli
from leo.config import load_config
from leo.graph.builder import build_graph
from leo.graph.responder import responder_messages
from leo.graph.state import chat_messages
from leo.graph.summary import recent_start, summarize_node
from leo.llm.gateway import LLMUnavailable
from tests.graph_fakes import FakeChat

CONVERSATION = load_config().conversation.model_copy(
    update={"summarize_after": 6, "keep_messages": 2})


# n user/Leo pairs with ids, as add_messages would give them.
def pairs(n: int) -> list:
    out = []
    for i in range(1, n + 1):
        out += [HumanMessage(f"q{i}", id=f"h{i}"), AIMessage(f"a{i}", id=f"a{i}")]
    return out


# At or below the limit nothing happens and the model is not called.
def test_no_summary_at_or_below_the_limit():
    chat = FakeChat("- summary")
    assert summarize_node({"messages": pairs(3)}, chat, keep=2, limit=6) == {}
    assert chat.calls == []


# Above the limit the older messages are removed, the last ones kept, and the
# old summary and the older messages go to the model as delimited data.
def test_older_messages_folded_into_the_summary():
    chat = FakeChat("- new summary")
    update = summarize_node({"messages": pairs(4), "summary": "- old"}, chat, keep=2, limit=6)
    assert update["summary"] == "- new summary"
    assert [m.id for m in update["messages"]] == ["h1", "a1", "h2", "a2", "h3", "a3"]
    data = chat.calls[0]["messages"][1]["content"]
    assert "<summary>\n- old\n</summary>" in data
    assert "User: q1\nLeo: a1" in data and "User: q3\nLeo: a3" in data and "q4" not in data


# The kept part starts with a user message (an unanswered message shifts the cut).
def test_cut_moves_forward_to_a_user_message():
    messages = [HumanMessage("x"), *pairs(2)]  # x was never answered
    assert recent_start(messages, 2) == 3
    assert recent_start(messages, 3) == 3
    assert recent_start([AIMessage("a")], 1) == 1


# A failed or empty summary call removes nothing and keeps the old summary.
def test_failed_summary_keeps_everything():
    # The model is not available.
    def failing(messages, output_model=None, force_cloud=False):
        raise LLMUnavailable("both down")

    assert summarize_node({"messages": pairs(4)}, failing, keep=2, limit=6) == {}
    assert summarize_node({"messages": pairs(4)}, FakeChat("  "), keep=2, limit=6) == {}


# With no summary the prompts are exactly as before M2.4.
def test_prompts_unchanged_without_a_summary():
    state = {"messages": pairs(1)}
    assert chat_messages("SYS", state) == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "q1"}, {"role": "assistant", "content": "a1"}]
    assert not any("Earlier in this conversation" in m["content"]
                   for m in responder_messages(state))


# The summary is one system line right after the system prompt, before the conversation.
def test_summary_line_in_agent_and_responder_prompts():
    state = {"messages": pairs(1), "summary": "- train 123"}
    line = {"role": "system", "content": "Earlier in this conversation:\n- train 123"}
    assert chat_messages("SYS", state)[1] == line
    assert responder_messages(state)[1] == line


# Through the graph: a long thread keeps a summary and only the recent messages,
# the next prompt carries the summary, and each reply is shown before the summary call.
def test_graph_keeps_summary_and_recent_messages():
    shown = []
    chat = FakeChat("reply")
    graph = build_graph(chat, checkpointer=InMemorySaver(), conversation=CONVERSATION)
    for i in range(1, 5):
        cli.run_turn(graph, [], f"message {i}", False, thread_id="t",
                     on_reply=lambda r: shown.append(len(chat.calls)))
    saved = graph.get_state({"configurable": {"thread_id": "t"}}).values
    assert saved["summary"] == "reply"  # the fake answers every call the same way
    assert [m.content for m in saved["messages"]] == ["message 4", "reply"]
    summary_calls = [i for i, c in enumerate(chat.calls)
                     if c["messages"][-1]["content"].startswith("<summary>")]
    assert len(summary_calls) == 1 and shown[-1] == summary_calls[0]
    cli.run_turn(graph, [], "message 5", False, thread_id="t")
    assert "Earlier in this conversation:\nreply" in [m["content"] for m in chat.calls[-1]["messages"]]
