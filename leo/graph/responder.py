"""The responder node: turns the conversation and agent results into one reply."""

from collections.abc import Callable

from langchain_core.messages import AIMessage

from leo.graph.state import LeoState, chat_messages

# Kept here until versioned prompt files arrive in M1.8.
SYSTEM_PROMPT = (
    "You are Leo, a helpful personal assistant. Reply in one or two short, "
    "speakable sentences. Use the same language as the user: English, Hindi "
    "or Hinglish. Use agent results if there are any; never invent facts."
)


# Ask the LLM for the reply and add it to the conversation. The provider,
# model and timings go in response_metadata so the CLI and reports can show them.
def responder_node(state: LeoState, chat: Callable, force_cloud: bool = False) -> dict:
    result = chat(chat_messages(SYSTEM_PROMPT, state), None, force_cloud)
    metadata = {
        "provider": result.provider,
        "model": result.model,
        "total_s": result.total_s,
        "first_token_s": result.first_token_s,
        "fallback_reason": result.fallback_reason,
    }
    return {"messages": [AIMessage(content=result.text, response_metadata=metadata)]}
