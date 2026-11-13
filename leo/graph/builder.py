"""Builds the LangGraph graph (architecture section 4.3, M1 subset).

  START -> supervisor -> <agent> -> supervisor ... -> responder -> END

M1.2 registers no agents, so a chat turn goes supervisor -> responder.
Agent nodes are passed in as plain functions; tests use a dummy one.
The LLM call can be sent to Groq per request with
config={"configurable": {"force_cloud": True}}.
"""

from collections.abc import Callable

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from leo.config import LeoConfig, load_config
from leo.graph.responder import responder_node
from leo.graph.state import LeoState
from leo.graph.supervisor import supervisor_node
from leo.llm import gateway


# Read the force_cloud flag from the run config (False when not set).
def _force_cloud(config: RunnableConfig) -> bool:
    return bool(config.get("configurable", {}).get("force_cloud", False))


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
        return supervisor_node(state, chat, list(agents), max_hops, _force_cloud(config))

    # Responder node with the LLM filled in.
    def responder(state: LeoState, config: RunnableConfig) -> dict:
        return responder_node(state, chat, _force_cloud(config))

    # Send the graph to the chosen agent, or to the responder on FINISH.
    def route(state: LeoState) -> str:
        choice = state.get("next_agent")
        return choice if choice in agents else "responder"

    graph = StateGraph(LeoState)
    graph.add_node("supervisor", supervisor)
    graph.add_node("responder", responder)
    for name, node in agents.items():
        graph.add_node(name, node)
        graph.add_edge(name, "supervisor")
    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges("supervisor", route, [*agents, "responder"])
    graph.add_edge("responder", END)
    # Each hop is two steps (supervisor, agent); leave room so max_hops, not
    # LangGraph's recursion limit, is what stops the loop.
    return graph.compile().with_config(recursion_limit=2 * max_hops + 5)
