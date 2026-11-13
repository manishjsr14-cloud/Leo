"""Tags and metadata put on every request trace: models and prompt versions.

Prompt versions are short hashes of each prompt's text (tracing.prompt_version)
until versioned prompt files arrive in M1.8.
"""

from functools import cache

from leo.agents import productivity
from leo.config import load_config
from leo.graph import responder, supervisor
from leo.ops.tracing import prompt_version


# (tags, metadata) for a request trace. Read once per process.
@cache
def request_tags() -> tuple[list[str], dict[str, str]]:
    llm = load_config().llm
    versions = {
        "supervisor": prompt_version(supervisor.SYSTEM_PROMPT),
        "responder": prompt_version(responder.SYSTEM_PROMPT),
        "productivity": prompt_version(productivity.SYSTEM_PROMPT),
    }
    tags = [f"model:{llm.primary.model}", f"fallback:{llm.fallback.model}"]
    tags += [f"prompt:{name}@{version}" for name, version in versions.items()]
    metadata = {"model": llm.primary.model, "fallback_model": llm.fallback.model,
                **{f"prompt_{name}": version for name, version in versions.items()}}
    return tags, metadata
