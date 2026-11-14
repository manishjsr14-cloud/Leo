"""Real get_weather tool: Open-Meteo geocoding + daily forecast (free, no key).

The place name is turned into coordinates first, then the daily forecast is
fetched in the configured time zone (IST). The code, not the model, labels each
day "today", "tomorrow" or its weekday, so the 4B model does no date maths.
Every result names Open-Meteo as its source (their licence asks for credit).
"""

from collections.abc import Callable
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from leo.config import ResearchConfig
from leo.tools.base import ToolError
from leo.tools.research_args import GetWeatherArgs
from leo.tools.research_tools import WEATHER_SOURCE, WEATHER_SOURCE_URL

DAILY = "precipitation_probability_max,precipitation_sum,temperature_2m_min,temperature_2m_max"


# "today", "tomorrow" or the weekday name for `day`, seen from `today`.
def day_label(day: date, today: date) -> str:
    if day == today:
        return "today"
    if day == today + timedelta(days=1):
        return "tomorrow"
    return day.strftime("%A")


# GET a JSON answer from Open-Meteo; network or HTTP errors become ToolError.
def get_json(client: httpx.Client, url: str, params: dict) -> dict:
    try:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise ToolError(f"weather service unavailable: {type(error).__name__}") from error


# Build the get_weather function. `today` can be swapped in tests.
def weather_functions(client: httpx.Client, settings: ResearchConfig,
                      today: Callable[[], date] | None = None) -> dict:
    zone = ZoneInfo(settings.timezone)
    today = today or (lambda: datetime.now(zone).date())

    # Find the place, fetch its forecast and return one labelled row per day.
    def get_weather(args: GetWeatherArgs) -> dict:
        found = get_json(client, settings.geocoding_url,
                         {"name": args.place, "count": 1, "language": "en", "format": "json"})
        if not found.get("results"):
            raise ToolError(f"no place named {args.place!r} found")
        place = found["results"][0]
        forecast = get_json(client, settings.forecast_url, {
            "latitude": place["latitude"], "longitude": place["longitude"],
            "daily": DAILY, "timezone": settings.timezone, "forecast_days": args.days})
        daily = forecast.get("daily", {})
        now = today()
        days = [{
            "date": day,
            "day": day_label(date.fromisoformat(day), now),
            "rain_chance_pct": daily["precipitation_probability_max"][i],
            "rain_mm": daily["precipitation_sum"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "temp_max_c": daily["temperature_2m_max"][i],
        } for i, day in enumerate(daily.get("time", []))]
        name = ", ".join(p for p in (place.get("name"), place.get("admin1"),
                                     place.get("country")) if p)
        return {"place": name, "days": days,
                "source": WEATHER_SOURCE, "source_url": WEATHER_SOURCE_URL}

    return {"get_weather": get_weather}
