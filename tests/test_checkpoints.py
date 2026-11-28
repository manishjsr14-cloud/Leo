"""M2.4 checkpoints: SqliteSaver in a temporary copy of Leo's database (never leo_data/)."""

from leo import cli
from leo.graph.builder import build_graph
from leo.memory.checkpoints import open_checkpointer, thread_values
from leo.memory.store import open_db
from tests.graph_fakes import FakeChat


# A graph on a fresh connection to the database file at `path`, as after a restart.
def graph_on(path, chat, agents=None):
    conn = open_db(path)
    return build_graph(chat, agents=agents, checkpointer=open_checkpointer(conn)), conn


# The texts of the messages saved in a thread.
def saved_texts(path, thread_id: str) -> list[str]:
    conn = open_db(path)
    try:
        return [m.content for m in thread_values(open_checkpointer(conn), thread_id)["messages"]]
    finally:
        conn.close()


# Two turns, a new connection (a restart), and the third turn sees the first two.
def test_conversation_continues_on_a_new_connection(tmp_path):
    db = tmp_path / "leo.db"
    chat = FakeChat("Hi Asha!", "Noted.", "Your name is Asha.")
    graph, conn = graph_on(db, chat)
    cli.run_turn(graph, [], "my name is Asha", False, thread_id="t1")
    cli.run_turn(graph, [], "I like tea", False, thread_id="t1")
    conn.close()
    graph, conn = graph_on(db, chat)
    reply, _ = cli.run_turn(graph, [], "what is my name?", False, thread_id="t1")
    conn.close()
    sent = [m["content"] for m in chat.calls[-1]["messages"]]
    assert sent[-6:-1] == ["my name is Asha", "Hi Asha!", "I like tea", "Noted.",
                           "what is my name?"]
    assert reply.content == "Your name is Asha."


# The checkpoint tables are in the same file as Leo's own tables.
def test_checkpoint_tables_share_the_database(tmp_path):
    graph, conn = graph_on(tmp_path / "leo.db", FakeChat("ok"))
    cli.run_turn(graph, [], "hello", False, thread_id="t1")
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"checkpoints", "writes", "memories", "tasks"} <= tables


# Two threads never see each other's messages.
def test_threads_are_separate(tmp_path):
    db = tmp_path / "leo.db"
    graph, conn = graph_on(db, FakeChat("one", "two"))
    cli.run_turn(graph, [], "first thread", False, thread_id="a")
    cli.run_turn(graph, [], "second thread", False, thread_id="b")
    conn.close()
    assert saved_texts(db, "a") == ["first thread", "one"]
    assert saved_texts(db, "b") == ["second thread", "two"]


# A saved thread does not hand one turn's plan or results to the next turn.
def test_per_request_fields_start_empty_each_turn(tmp_path):
    # An agent that records the results it saw and adds its own.
    def agent(state):
        seen.append(dict(state.get("agent_results") or {}))
        return {"agent_results": {"productivity": "done"}}

    seen: list = []
    plan = {"agents": ["productivity"], "task": "do it"}
    chat = FakeChat(plan, "Reply.", plan, "Reply.")
    graph, conn = graph_on(tmp_path / "leo.db", chat, {"productivity": agent})
    cli.run_turn(graph, [], "please do it", False, thread_id="t1")
    cli.run_turn(graph, [], "please do it", False, thread_id="t1")
    conn.close()
    assert seen == [{}, {}]


# A turn that stops halfway (here the model fails) leaves the user's message in
# the thread with no reply; the next turn still works (a known limit, M2.4).
def test_half_finished_turn_leaves_an_unanswered_message(tmp_path):
    db = tmp_path / "leo.db"

    # The responder's model fails on the first call, then answers.
    def flaky(messages, output_model=None, force_cloud=False):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("killed")
        return FakeChat("answered")(messages, output_model, force_cloud)

    calls: list = []
    graph, conn = graph_on(db, flaky)
    try:
        cli.run_turn(graph, [], "first question", False, thread_id="t1")
    except RuntimeError:
        pass
    reply, _ = cli.run_turn(graph, [], "second question", False, thread_id="t1")
    conn.close()
    assert reply.content == "answered"
    assert saved_texts(db, "t1") == ["first question", "second question", "answered"]
