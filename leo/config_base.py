"""The base class for config sections (see leo/config.py)."""

from pydantic import BaseModel, ConfigDict


class Strict(BaseModel):
    """Base for config sections: unknown keys are an error, so typos are caught."""

    model_config = ConfigDict(extra="forbid")
