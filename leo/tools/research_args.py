"""Argument schemas for the research tools (architecture sections 9 and 12.3).

Shared by the real and mock tools. Unknown keys are refused
(ToolArgs uses extra="forbid").
"""

from urllib.parse import urlsplit

from pydantic import Field, field_validator

from leo.tools.base import ToolArgs


class WebSearchArgs(ToolArgs):
    """Arguments for web_search: what to search for and how many results."""

    query: str = Field(min_length=1, max_length=200)
    max_results: int = Field(default=5, ge=1, le=5)


class ReadPageArgs(ToolArgs):
    """Arguments for read_page: an http or https address with a host name."""

    url: str = Field(min_length=1, max_length=2000)

    # Only web addresses: no file://, ftp:// or addresses without a host.
    @field_validator("url")
    @classmethod
    def http_only(cls, url: str) -> str:
        parts = urlsplit(url.strip())
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ValueError("url must start with http:// or https:// and name a host")
        return url.strip()


class GetWeatherArgs(ToolArgs):
    """Arguments for get_weather: a place name and how many days from today."""

    place: str = Field(min_length=1, max_length=100)
    days: int = Field(default=3, ge=1, le=7)
