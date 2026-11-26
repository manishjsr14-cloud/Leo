"""Config sections for the LLM tiers (config.yaml `llm:`). Loaded by leo/config.py."""

from typing import Literal

from pydantic import Field

from leo.config_base import Strict


class PrimaryLLM(Strict):
    """The local model on the laptop GPU."""

    provider: Literal["ollama"]
    model: str
    base_url: str
    num_ctx: int = Field(gt=0)
    think: bool
    temperature: float = Field(ge=0, le=2)   # sent on every request (M1 exit check)
    first_token_timeout_s: float = Field(gt=0)
    total_timeout_s: float = Field(gt=0)
    max_bad_outputs: int = Field(ge=1)
    warm_up: bool = True          # one tiny request at startup loads the model (M1 cleanup)


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
