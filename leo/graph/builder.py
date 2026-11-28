"""Builds the LangGraph graph (architecture section 4.3, M1 subset).

  START -> supervisor -> <agent 1> -> <agent 2> ... -> responder -> END

With a memory bank (M2.3) the graph starts with memory_recall and ends with
memory_write:
  START -> memory_recall -> supervisor -> ... -> responder -> memory_write -> END

The supervisor plans the agent list once (agent_queue); the graph runs those
agents in order, each seeing the earlier agents' results, then the responder.
graph.max_hops caps how many agents run. With an empty plan the supervisor
goes straight to the responder.
Agent nodes are passed in as plain functions; tests use a dummy one.
The LLM call can be sent to Groq per request with
config={"configurable": {"force_cloud": True}}.
Every node runs inside a tracing span named after it (section 13.2).
With a checkpointer (M2.4) the state is saved per thread_id after every step
(config={"configurable": {"thread_id": ...}}); with a conversation config the
graph ends with the rolling summary (leo/graph/summary.py):
  ... -> responder [-> memory_write] -> summarize -> END
"""

from collections.abc import Callable

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from leo.config import ConversationConfig, LeoConfig, load_config
from leo.graph import responder as responder_module
from leo.graph import supervisor as supervisor_module
from leo.graph.node_wiring import (
    add_memory_nodes,
    add_summary_node,
    cloud_requested,
    traced,
)
from leo.graph.responder import responder_node
from leo.graph.state import LeoState
from leo.graph.supervisor import supervisor_node
from leo.llm import gateway
from leo.memory.memories import MemoryBank


# Build and compile the graph. chat defaults to the real LLM gateway;
# agents maps an agent name to its node function; memory (M2.3) adds the
# memory_recall and memory_write nodes, and without it the graph is as before;
# now (M2.3c) gives the responder the current time (default: the real clock);
# checkpointer (M2.4) saves the state per thread; conversation (M2.4) adds the summary.
def build_graph(
    chat: Callable | None = None,
    agents: dict[str, Callable] | None = None,
    config: LeoConfig | None = None,
    memory: MemoryBank | None = None,
    now: Callable | None = None,
    checkpointer=None,
    conversation: ConversationConfig | None = None,
):
    chat = chat or gateway.chat
    agents = agents or {}
    max_hops = (config or load_config()).graph.max_hops

    # Supervisor node with the LLM, agent names and hop limit filled in.
    def supervisor(state: LeoState, config: RunnableConfig) -> dict:
        return supervisor_node(state, chat, list(agents), cloud_requested(config))

    # Responder node with the LLM filled in.
    def responder(state: LeoState, config: RunnableConfig) -> dict:
        return responder_node(state, chat, cloud_requested(config), now() if now else None)

    # The next planned agent, or the responder when the plan is used up or
    # max_hops agents have run.
    def route(state: LeoState) -> str:
        queue, hops = state.get("agent_queue") or [], state.get("hops", 0)
        if hops >= max_hops or hops >= len(queue) or queue[hops] not in agents:
            return "responder"
        return queue[hops]

    # Run an agent node and count it as one hop.
    def counted(node: Callable) -> Callable:
        # The agent's own update plus the new hop count.
        def run(state: LeoState, config: RunnableConfig) -> dict:
            return {**node(state, config), "hops": state.get("hops", 0) + 1}
        return run

    graph = StateGraph(LeoState)
    graph.add_node("supervisor", traced("supervisor", "chain", supervisor, {
        "prompt_version": supervisor_module.PROMPT.tag}))
    graph.add_node("responder", traced("responder", "chain", responder, {
        "prompt_version": responder_module.PROMPT.tag}))
    for name, node in agents.items():
        graph.add_node(name, counted(traced(name, "agent", node)))
    for source in ["supervisor", *agents]:
        graph.add_conditional_edges(source, route, [*agents, "responder"])
    last = END
    if conversation is not None:
        add_summary_node(graph, chat, conversation)
        last = "summarize"
    if memory is None:
        graph.add_edge(START, "supervisor")
        graph.add_edge("responder", last)
    else:
        add_memory_nodes(graph, memory, chat, last)
    # One step per agent plus supervisor and responder; leave room so max_hops,
    # not LangGraph's recursion limit, is what stops a run.
    return graph.compile(checkpointer=checkpointer).with_config(recursion_limit=2 * max_hops + 5)
