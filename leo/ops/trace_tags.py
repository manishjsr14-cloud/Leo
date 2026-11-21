"""Tags and metadata put on every request trace: models and prompt versions.

Prompt versions come from the versioned prompt files (prompts/*.yaml, M1.8),
e.g. the tag "prompt:calendar@1" and the metadata prompt_calendar = "1".
"""

from functools import cache

from leo.config import load_config
from leo.llm.prompts import load_prompt

PROMPT_NAMES = ["supervisor", "responder", "replies", "productivity", "research", "calendar"]


# (tags, metadata) for a request trace. Read once per process.
@cache
def request_tags() -> tuple[list[str], dict[str, str]]:
    llm = load_config().llm
    prompts = [load_prompt(name) for name in PROMPT_NAMES]
    tags = [f"model:{llm.primary.model}", f"fallback:{llm.fallback.model}"]
    tags += [f"prompt:{p.tag}" for p in prompts]
    metadata = {"model": llm.primary.model, "fallback_model": llm.fallback.model,
                **{f"prompt_{p.name}": str(p.version) for p in prompts}}
    return tags, metadata
