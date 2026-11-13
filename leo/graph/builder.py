"""Builds the LangGraph graph (architecture section 4.3, M1 subset).

  START -> supervisor -> <agent> -> supervisor ... -> responder -> END

M1.2 registers no agents, so a chat turn goes supervisor -> responder.
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


# Wrap a node in a span named after it. The span gets `metadata` and, when the
# node routes, the chosen agent's name (never text). Nodes that take only the
# state (simple test agents) are called without the run config.
def traced(name: str, kind: str, fn: Callable, metadata: dict | None = None) -> Callable:
    takes_config = len(inspect.signature(fn).parameters) >= 2

    # The node LangGraph calls.
    def node(state: LeoState, config: RunnableConfig) -> dict:
        with tracing.span(name, kind, metadata=metadata) as span:
            update = fn(state, config) if takes_config else fn(state)
            if "next_agent" in update:
                span.update(metadata={**(metadata or {}), "next": update["next_agent"]})
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
        return supervisor_node(state, chat, list(agents), max_hops, cloud_requested(config))

    # Responder node with the LLM filled in.
    def responder(state: LeoState, config: RunnableConfig) -> dict:
        return responder_node(state, chat, cloud_requested(config))

    # Send the graph to the chosen agent, or to the responder on FINISH.
    def route(state: LeoState) -> str:
        choice = state.get("next_agent")
        return choice if choice in agents else "responder"

    graph = StateGraph(LeoState)
    graph.add_node("supervisor", traced("supervisor", "chain", supervisor, {
        "prompt_version": tracing.prompt_version(supervisor_module.SYSTEM_PROMPT)}))
    graph.add_node("responder", traced("responder", "chain", responder, {
        "prompt_version": tracing.prompt_version(responder_module.SYSTEM_PROMPT)}))
    for name, node in agents.items():
        graph.add_node(name, traced(name, "agent", node))
        graph.add_edge(name, "supervisor")
    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges("supervisor", route, [*agents, "responder"])
    graph.add_edge("responder", END)
    # Each hop is two steps (supervisor, agent); leave room so max_hops, not
    # LangGraph's recursion limit, is what stops the loop.
    return graph.compile().with_config(recursion_limit=2 * max_hops + 5)
