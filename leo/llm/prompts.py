"""Versioned prompt files (prompts/*.yaml, architecture section 18, M1.8).

Each file has a name, a whole-number version, the system text and optional
few-shot examples:
  name: calendar
  version: 1
  system: |            # may hold {placeholders}, filled in with render()
    ...
  examples: [...]      # added after the text as "Examples:" lines, unformatted
Other keys (the supervisor's agent list, the reply templates) are kept as
they are and read by the code that owns the file. A change to a prompt's text
needs a new version number; traces carry the tag, e.g. "calendar@1".
"""

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


class Prompt(BaseModel):
    """One prompt file."""

    model_config = ConfigDict(extra="allow", frozen=True)

    name: str
    version: int = Field(ge=1)
    system: str = ""
    examples: list[str] = []

    # "calendar@1": the tag put on traces.
    @property
    def tag(self) -> str:
        return f"{self.name}@{self.version}"

    # The system text with its placeholders filled in, then the examples.
    def render(self, **values) -> str:
        text = self.system.format(**values).rstrip()
        if self.examples:
            text += "\nExamples:\n" + "\n".join(f"- {e}" for e in self.examples)
        return text

    # Another key of the file (e.g. "agents" or "en"), or `default`.
    def extra(self, key: str, default=None):
        return (self.model_extra or {}).get(key, default)


# Read prompts/<name>.yaml once. The file's own name must match.
@lru_cache
def load_prompt(name: str, folder: Path = PROMPTS_DIR) -> Prompt:
    data = yaml.safe_load((folder / f"{name}.yaml").read_text(encoding="utf-8"))
    prompt = Prompt.model_validate(data)
    if prompt.name != name:
        raise ValueError(f"prompts/{name}.yaml says name: {prompt.name}")
    return prompt
