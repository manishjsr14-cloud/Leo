"""The 3 real research tools in one list: web_search, read_page, get_weather.

They share one httpx client with the configured timeout. Tests build the
tools from web.py and weather.py directly, with fake transports.
"""

import httpx

from leo.config import ResearchConfig
from leo.tools.base import Tool
from leo.tools.real.weather import weather_functions
from leo.tools.real.web import web_functions
from leo.tools.research_tools import make_tools

USER_AGENT = "Leo-personal-assistant/0.1"


# Build the real research tools on a new httpx client.
def real_research_tools(settings: ResearchConfig) -> list[Tool]:
    client = httpx.Client(timeout=settings.timeout_s, headers={"User-Agent": USER_AGENT})
    return make_tools({**web_functions(client, settings),
                       **weather_functions(client, settings)})
