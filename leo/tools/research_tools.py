"""Names, descriptions and tiers of the 3 research tools (section 9: all 🟢).

The real and mock versions use this one list, so they can never drift apart.
News tools (get_headlines, search_news, ...) come with M2.10.
"""

from leo.tools.base import Tier, Tool
from leo.tools.research_args import GetWeatherArgs, ReadPageArgs, WebSearchArgs

# Where weather data comes from; the reply must name it (section 12.4, groundedness).
WEATHER_SOURCE = "Open-Meteo"
WEATHER_SOURCE_URL = "https://open-meteo.com"
SEARCH_SOURCE = "DuckDuckGo"

# name -> (description, argument schema)
SPECS = {
    "web_search": ("Search the web. Returns results with their url and a short text.",
                   WebSearchArgs),
    "read_page": ("Read the main text of one web page, by its http(s) url.", ReadPageArgs),
    "get_weather": (
        ("Weather forecast for a place for today, tomorrow and the day after: "
         "rain chance, rain mm, min/max temperature."),
        GetWeatherArgs,
    ),
}


# Turn a name -> function dict into Tool objects, all 🟢 SAFE and read-only (M2.3c).
def make_tools(functions: dict) -> list[Tool]:
    if set(functions) != set(SPECS):
        raise ValueError(f"functions must be exactly {sorted(SPECS)}")
    return [
        Tool(name=name, description=description, tier=Tier.SAFE, args_model=args_model,
             fn=functions[name], read_only=True)
        for name, (description, args_model) in SPECS.items()
    ]
