"""Builds the LangGraph graph (architecture section 4.3, M1 subset).

  START -> supervisor -> <agent 1> -> <agent 2> ... -> responder -> END

The supervisor plans the agent list once (agent_queue); the graph runs those
agents in order, each seeing the earlier agents' results, then the responder.
graph.max_hops caps how many agents run. With an empty plan the supervisor
goes straight to the responder.
Agent nodes are passed in as plain functions; tests use a dummy one.
The LLM call can be sent to Groq per request with
config={"configurable": {"force_cloud": True}}.
Every node runs inside a tracing span named after it (section 13.2).
"""

import inspect
from collections.abc import Callable

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from leo.config import LeoConfig, load_config
from leo.graph import responder as responder_module
from leo.graph import supervisor as supervisor_module
from leo.graph.responder import responder_node
from leo.graph.state import LeoState
from leo.graph.supervisor import supervisor_node
from leo.llm import gateway
from leo.ops import tracing


# Read the force_cloud flag from the run config (False when not set).
def cloud_requested(config: RunnableConfig) -> bool:
    return bool(config.get("configurable", {}).get("force_cloud", False))


# Wrap a node in a span named after it. The span gets `metadata` and, for the
# supervisor, the planned agent names (never text). Nodes that take only the
# state (simple test agents) are called without the run config.
def traced(name: str, kind: str, fn: Callable, metadata: dict | None = None) -> Callable:
    takes_config = len(inspect.signature(fn).parameters) >= 2

    # The node LangGraph calls.
    def node(state: LeoState, config: RunnableConfig) -> dict:
        with tracing.span(name, kind, metadata=metadata) as span:
            update = fn(state, config) if takes_config else fn(state)
            if "agent_queue" in update:
                span.update(metadata={**(metadata or {}), "plan": update["agent_queue"]})
            return update

    return node


# Build and compile the graph. chat defaults to the real LLM gateway;
# agents maps an agent name to its node function.
def build_graph(
    chat: Callable | None = None,
    agents: dict[str, Callable] | None = None,
    config: LeoConfig | None = None,
):
    chat = chat or gateway.chat
    agents = agents or {}
    max_hops = (config or load_config()).graph.max_hops

    # Supervisor node with the LLM, agent names and hop limit filled in.
    def supervisor(state: LeoState, config: RunnableConfig) -> dict:
        return supervisor_node(state, chat, list(agents), cloud_requested(config))

    # Responder node with the LLM filled in.
    def responder(state: LeoState, config: RunnableConfig) -> dict:
        return responder_node(state, chat, cloud_requested(config))

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
        "prompt_version": tracing.prompt_version(supervisor_module.SYSTEM_PROMPT)}))
    graph.add_node("responder", traced("responder", "chain", responder, {
        "prompt_version": tracing.prompt_version(responder_module.SYSTEM_PROMPT)}))
    graph.add_edge(START, "supervisor")
    for name, node in agents.items():
        graph.add_node(name, counted(traced(name, "agent", node)))
    for source in ["supervisor", *agents]:
        graph.add_conditional_edges(source, route, [*agents, "responder"])
    graph.add_edge("responder", END)
    # One step per agent plus supervisor and responder; leave room so max_hops,
    # not LangGraph's recursion limit, is what stops a run.
    return graph.compile().with_config(recursion_limit=2 * max_hops + 5)
