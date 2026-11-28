"""Config sections for the server, graph, conversation, storage, embedder, agents and tracing.

Loaded by leo/config.py; relative paths start at the project folder.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from leo.config_base import Strict
from leo.paths import PROJECT_ROOT


class ServerConfig(Strict):
    """Where the API listens and how devices log in."""

    host: str
    port: int = Field(gt=0, lt=65536)
    auth: Literal["device_tokens"]


class GraphConfig(Strict):
    """Limits for the LangGraph agent loop."""

    max_hops: int = Field(ge=1)


class ConversationConfig(Strict):
    """One conversation thread and its rolling summary (M2.4)."""

    thread_id: str = Field(min_length=1)  # the CLI's default thread
    summarize_after: int = Field(ge=2)    # more messages than this: summarize the older ones
    keep_messages: int = Field(ge=2)      # the last messages kept as they are

    # Keeping must leave something to summarize.
    @model_validator(mode="after")
    def keep_fewer_than_limit(self):
        if self.keep_messages >= self.summarize_after:
            raise ValueError("keep_messages must be smaller than summarize_after")
        return self


class StorageConfig(Strict):
    """Where Leo's SQLite file lives. A relative path is under the project folder."""

    db_path: Path

    # The database path as an absolute path (relative paths start at the project folder).
    def resolved_db_path(self) -> Path:
        return self.db_path if self.db_path.is_absolute() else PROJECT_ROOT / self.db_path


class EmbedderConfig(Strict):
    """The shared e5 embedder (section 8.1). CPU only: the GPU is kept for Ollama."""

    model: str
    device: Literal["cpu"]
    dimension: int = Field(gt=0)
    cache_dir: Path
    query_prefix: str
    passage_prefix: str
    cache_size: int = Field(ge=1)

    # The model cache folder as an absolute path (relative paths start at the project folder).
    def resolved_cache_dir(self) -> Path:
        return self.cache_dir if self.cache_dir.is_absolute() else PROJECT_ROOT / self.cache_dir


class AgentConfig(Strict):
    """Limits for one specialist agent run."""

    max_steps: int = Field(ge=1)


class TracingConfig(Strict):
    """Langfuse tracing. Without include_text, traces hold no message text."""

    include_text: bool = False
    timeout_s: int = Field(default=5, ge=1)


class MemoryConfig(Strict):
    """Long-term memory (M2.3, M2.3b): how many memories are searched and given as hints."""

    search_k: int = Field(ge=1)          # nearest memories looked at per message
    recall_k: int = Field(ge=1)          # this many nearest become hints (personal questions)
    candidate_subjects: int = Field(ge=1)  # nearby subjects shown to the extraction step
