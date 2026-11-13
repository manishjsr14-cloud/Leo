"""A fake gateway.chat for graph tests. No network is used.

Each call records (messages, output_model, force_cloud) and returns the next
planned reply. A reply is a string, or a SupervisorDecision-style dict that is
returned as parsed JSON. When the plan runs out, the last reply repeats.
"""

import json

from leo.llm.gateway import LLMResult


# Build an LLMResult like the gateway would, with fixed timings.
def llm_result(text: str, parsed=None, valid: bool = True, provider: str = "ollama") -> LLMResult:
    return LLMResult(
        text=text, parsed=parsed, valid=valid, provider=provider, model="fake",
        prompt_tokens=1, completion_tokens=1, first_token_s=0.1, total_s=0.2,
        thinking_seen=False,
    )


class FakeChat:
    """Stands in for leo.llm.gateway.chat and records every call."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls: list[dict] = []

    # Record the call and return the next planned reply.
    def __call__(self, messages, output_model=None, force_cloud=False):
        self.calls.append(
            {"messages": messages, "output_model": output_model, "force_cloud": force_cloud}
        )
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        provider = "groq" if force_cloud else "ollama"
        if isinstance(reply, dict) and output_model is not None:
            return llm_result(json.dumps(reply), output_model(**reply), provider=provider)
        if reply is None:
            return llm_result("not json", valid=False, provider=provider)
        return llm_result(str(reply), provider=provider)
