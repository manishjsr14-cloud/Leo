"""Load and check Leo's settings.

config.yaml holds models, URLs and thresholds. .env holds secrets.
Both are checked with Pydantic so a typo fails at startup, not mid-request.
The section models live in leo/config_llm.py, config_sections.py and
config_tools.py (split to keep files short); they are imported here, so
callers keep importing everything from leo.config.
"""

from pathlib import Path

import yaml
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from leo.config_base import Strict
from leo.config_llm import DesktopLLM, FallbackLLM, LLMConfig, PrimaryLLM
from leo.config_sections import (
    AgentConfig,
    EmbedderConfig,
    GraphConfig,
    ServerConfig,
    StorageConfig,
    TracingConfig,
)
from leo.config_tools import CalendarConfig, LanguageConfig, ResearchConfig
from leo.paths import PROJECT_ROOT

__all__ = [
    "CONFIG_PATH",
    "ENV_PATH",
    "PROJECT_ROOT",
    "AgentConfig",
    "CalendarConfig",
    "DesktopLLM",
    "EmbedderConfig",
    "FallbackLLM",
    "GraphConfig",
    "LLMConfig",
    "LanguageConfig",
    "LeoConfig",
    "PrimaryLLM",
    "ResearchConfig",
    "Secrets",
    "ServerConfig",
    "StorageConfig",
    "Strict",
    "TracingConfig",
    "load_config",
    "load_secrets",
]

CONFIG_PATH = PROJECT_ROOT / "config.yaml"
ENV_PATH = PROJECT_ROOT / ".env"


class LeoConfig(Strict):
    """The whole config.yaml file."""

    llm: LLMConfig
    ollama_env: dict[str, str]
    server: ServerConfig
    graph: GraphConfig
    storage: StorageConfig
    embedder: EmbedderConfig
    agent: AgentConfig
    tracing: TracingConfig
    research: ResearchConfig
    language: LanguageConfig
    calendar: CalendarConfig
    machines: dict[str, str]  # machine label -> text found in its nvidia-smi GPU name


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
