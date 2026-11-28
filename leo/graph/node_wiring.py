"""Small helpers that add nodes to Leo's graph (split out of builder.py, M2.4).

cloud_requested reads the per-request Groq flag; traced wraps a node in a
tracing span; add_memory_nodes and add_summary_node add the optional memory
(M2.3) and rolling-summary (M2.4) nodes.
"""

import inspect
from collections.abc import Callable

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from leo.config import ConversationConfig
from leo.graph import memory_nodes as memory_module
from leo.graph import summary as summary_module
from leo.graph.memory_nodes import memory_recall_node, memory_write_node
from leo.graph.state import LeoState
from leo.graph.summary import summarize_node
from leo.memory.memories import MemoryBank
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


# Add memory_recall before the supervisor and memory_write after the responder;
# memory_write goes on to `last` (END, or the summary node).
def add_memory_nodes(graph: StateGraph, bank: MemoryBank, chat: Callable, last: str) -> None:
    # Recall node with the memory bank filled in.
    def recall(state: LeoState) -> dict:
        return memory_recall_node(state, bank)

    # Write node with the memory bank and the LLM filled in.
    def write(state: LeoState, config: RunnableConfig) -> dict:
        return memory_write_node(state, bank, chat, cloud_requested(config))

    graph.add_node("memory_recall", traced("memory_recall", "chain", recall))
    graph.add_node("memory_write", traced("memory_write", "chain", write, {
        "prompt_version": memory_module.PROMPT.tag}))
    graph.add_edge(START, "memory_recall")
    graph.add_edge("memory_recall", "supervisor")
    graph.add_edge("responder", "memory_write")
    graph.add_edge("memory_write", last)


# Add the summarize node, which ends the graph (M2.4).
def add_summary_node(graph: StateGraph, chat: Callable, conversation: ConversationConfig) -> None:
    # Summary node with the LLM and the limits filled in.
    def summarize(state: LeoState, config: RunnableConfig) -> dict:
        return summarize_node(state, chat, conversation.keep_messages,
                              conversation.summarize_after, cloud_requested(config))

    graph.add_node("summarize", traced("summarize", "chain", summarize, {
        "prompt_version": summary_module.PROMPT.tag}))
    graph.add_edge("summarize", END)
