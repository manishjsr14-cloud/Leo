"""Load and check Leo's settings.

config.yaml holds models, URLs and thresholds. .env holds secrets.
Both are checked with Pydantic so a typo fails at startup, not mid-request.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
ENV_PATH = PROJECT_ROOT / ".env"


class Strict(BaseModel):
    """Base for config sections: unknown keys are an error, so typos are caught."""

    model_config = ConfigDict(extra="forbid")


class PrimaryLLM(Strict):
    """The local model on the laptop GPU."""

    provider: Literal["ollama"]
    model: str
    base_url: str
    num_ctx: int = Field(gt=0)
    think: bool
    first_token_timeout_s: float = Field(gt=0)
    total_timeout_s: float = Field(gt=0)
    max_bad_outputs: int = Field(ge=1)


class DesktopLLM(Strict):
    """The optional backup model on the gaming desktop."""

    provider: Literal["ollama"]
    model: str
    base_url: str
    num_ctx: int = Field(gt=0)
    think: bool


class FallbackLLM(Strict):
    """The Groq cloud model used when the local model fails."""

    provider: Literal["groq"]
    model: str
    base_url: str
    reasoning_effort: Literal["low", "medium", "high"]
    timeout_s: float = Field(gt=0)
    max_retries: int = Field(ge=0)


class LLMConfig(Strict):
    """All LLM tiers plus the risk threshold for escalation."""

    primary: PrimaryLLM
    desktop: DesktopLLM
    fallback: FallbackLLM
    escalate_risk_threshold: float = Field(ge=0, le=1)


class ServerConfig(Strict):
    """Where the API listens and how devices log in."""

    host: str
    port: int = Field(gt=0, lt=65536)
    auth: Literal["device_tokens"]


class GraphConfig(Strict):
    """Limits for the LangGraph agent loop."""

    max_hops: int = Field(ge=1)


class StorageConfig(Strict):
    """Where Leo's SQLite file lives. A relative path is under the project folder."""

    db_path: Path

    # The database path as an absolute path (relative paths start at the project folder).
    def resolved_db_path(self) -> Path:
        return self.db_path if self.db_path.is_absolute() else PROJECT_ROOT / self.db_path


class AgentConfig(Strict):
    """Limits for one specialist agent run."""

    max_steps: int = Field(ge=1)


class TracingConfig(Strict):
    """Langfuse tracing. Without include_text, traces hold no message text."""

    include_text: bool = False
    timeout_s: int = Field(default=5, ge=1)


class ResearchConfig(Strict):
    """URLs and limits for web search, page reading and weather."""

    geocoding_url: str
    forecast_url: str
    timezone: str
    timeout_s: float = Field(gt=0)
    max_redirects: int = Field(ge=0, le=10)
    max_page_bytes: int = Field(gt=0)
    max_page_chars: int = Field(gt=0)


class LanguageConfig(Strict):
    """Indian time parser: the time zone used when no "now" is given."""

    timezone: str


class CalendarConfig(Strict):
    """Calendar agent: default event length and the part-of-day windows."""

    default_event_minutes: int = Field(ge=1)
    day_parts: dict[Literal["morning", "afternoon", "evening", "night"], tuple[int, int]]

    # Each window must be whole hours inside the day, start before end.
    @field_validator("day_parts")
    @classmethod
    def windows_inside_day(cls, parts: dict) -> dict:
        for name, (start, end) in parts.items():
            if not 0 <= start < end <= 24:
                raise ValueError(f"day_parts.{name} must be 0 <= start < end <= 24")
        return parts


class LeoConfig(Strict):
    """The whole config.yaml file."""

    llm: LLMConfig
    ollama_env: dict[str, str]
    server: ServerConfig
    graph: GraphConfig
    storage: StorageConfig
    agent: AgentConfig
    tracing: TracingConfig
    research: ResearchConfig
    language: LanguageConfig
    calendar: CalendarConfig


class Secrets(BaseSettings):
    """API keys read from .env. SecretStr hides them when printed."""

    model_config = SettingsConfigDict(env_file=ENV_PATH, extra="ignore")

    groq_api_key: SecretStr = SecretStr("")
    langfuse_public_key: SecretStr = SecretStr("")
    langfuse_secret_key: SecretStr = SecretStr("")
    langfuse_host: str = ""


# Read config.yaml (or another YAML file) and return the checked settings.
def load_config(path: Path = CONFIG_PATH) -> LeoConfig:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return LeoConfig.model_validate(data)


# Read the secrets from .env and the environment.
def load_secrets() -> Secrets:
    return Secrets()
