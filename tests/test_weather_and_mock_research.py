"""Tests for leo/tools/real/weather.py (httpx.MockTransport, no network) and the
mock research tools."""

from datetime import date

import httpx
import pytest
from pydantic import ValidationError

from leo.config import load_config
from leo.guardrails.context_guard import END
from leo.tools.base import ToolError
from leo.tools.mock.research import INJECTION, mock_research_tools
from leo.tools.real.weather import weather_functions
from leo.tools.registry import by_name, call_tool
from leo.tools.research_args import GetWeatherArgs

SETTINGS = load_config().research
PUNE = {"results": [{"name": "Pune", "latitude": 18.52, "longitude": 73.86,
                     "admin1": "Maharashtra", "country": "India"}]}
FORECAST = {"daily": {
    "time": ["2026-11-14", "2026-11-15", "2026-11-16"],
    "precipitation_probability_max": [5, 60, 10],
    "precipitation_sum": [0.0, 3.4, 0.0],
    "temperature_2m_min": [15.2, 16.0, 15.8],
    "temperature_2m_max": [30.1, 28.4, 29.9]}}


# get_weather on a MockTransport; `geo` is the geocoding answer. Requests are kept.
def weather(geo: dict = PUNE, status: int = 200):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.host.startswith("geocoding"):
            return httpx.Response(status, json=geo)
        return httpx.Response(status, json=FORECAST)
    client = httpx.Client(transport=httpx.MockTransport(handler))
    fn = weather_functions(client, SETTINGS, today=lambda: date(2026, 11, 14))
    return fn["get_weather"], seen


def test_pune_forecast_rows_are_labelled_with_source():
    get_weather, seen = weather()
    out = get_weather(GetWeatherArgs(place="Pune"))
    assert out["place"] == "Pune, Maharashtra, India"
    assert [d["day"] for d in out["days"]] == ["today", "tomorrow", "Monday"]
    assert out["days"][1]["rain_chance_pct"] == 60
    assert out["source"] == "Open-Meteo" and out["source_url"] == "https://open-meteo.com"
    forecast = seen[1].url.params
    assert forecast["timezone"] == "Asia/Kolkata" and forecast["forecast_days"] == "3"
    assert forecast["latitude"] == "18.52"


def test_unknown_place_and_service_errors_give_tool_errors():
    get_weather, _ = weather(geo={})
    with pytest.raises(ToolError, match="no place named 'Atlantis'"):
        get_weather(GetWeatherArgs(place="Atlantis"))
    get_weather, _ = weather(status=503)
    with pytest.raises(ToolError, match="weather service unavailable"):
        get_weather(GetWeatherArgs(place="Pune"))


# get_weather takes only the place: the model cannot pick the number of days.
def test_weather_args_take_only_a_place():
    for extra in ({"days": 1}, {"units": "F"}):
        with pytest.raises(ValidationError):
            GetWeatherArgs(place="Pune", **extra)


def test_mock_research_tools_log_calls_and_wrap_web_text():
    log = []
    tools = by_name(mock_research_tools(log))
    weather_out = call_tool(tools, "get_weather", {"place": "pune"})
    page = call_tool(tools, "read_page", {"url": "https://example.com/pune-monsoon"})
    search = call_tool(tools, "web_search", {"query": "pune rain", "max_results": 1})
    assert [c.tool for c in log] == ["get_weather", "read_page", "web_search"]
    assert [d["day"] for d in weather_out["days"]] == ["today", "tomorrow", "Monday"]
    assert INJECTION in page["text"] and page["text"].endswith(END)
    assert len(search["results"]) == 1 and search["results"][0]["url"].startswith("https://")
