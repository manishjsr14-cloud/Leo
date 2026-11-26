"""Config sections for the research tools, the language parser and the calendar.

Loaded by leo/config.py.
"""

from typing import Literal

from pydantic import Field, field_validator

from leo.config_base import Strict


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
    """Time parser zone, and the share of Hindi words that tags a message Hinglish."""

    timezone: str
    hinglish_min_ratio: float = Field(gt=0, le=1)


class CalendarConfig(Strict):
    """Calendar agent: default event length and the part-of-day windows."""

    default_event_minutes: int = Field(ge=1)
    day_parts: dict[Literal["morning", "afternoon", "evening", "night"], tuple[int, int]]
    waking_hours: tuple[int, int]  # free time for a whole day is looked for only here
    rain_skip_percent: int = Field(ge=0, le=100)  # "if it won't rain": no event above this

    # Each window must be whole hours inside the day, start before end.
    @field_validator("day_parts")
    @classmethod
    def windows_inside_day(cls, parts: dict) -> dict:
        for name, (start, end) in parts.items():
            if not 0 <= start < end <= 24:
                raise ValueError(f"day_parts.{name} must be 0 <= start < end <= 24")
        return parts

    # Waking hours are whole hours inside the day, start before end.
    @field_validator("waking_hours")
    @classmethod
    def waking_inside_day(cls, hours: tuple[int, int]) -> tuple[int, int]:
        if not 0 <= hours[0] < hours[1] <= 24:
            raise ValueError("waking_hours must be 0 <= start < end <= 24")
        return hours
