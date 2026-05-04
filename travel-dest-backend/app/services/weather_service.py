"""Weather lookup service built on top of Open-Meteo APIs."""
# uses injected async http client and settings for API calls

import time
from typing import Any

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.core.logging import get_logger


logger = get_logger(__name__)

WEATHER_CODE_SUMMARIES = {
    0: "clear skies",
    1: "mostly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    51: "light drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "light snow",
    80: "rain showers",
    95: "thunderstorms",
}


class WeatherService:
    """Fetch and cache lightweight weather summaries for destinations."""

    def __init__(self, http_client: httpx.AsyncClient, settings: Settings) -> None:
        """Store the shared HTTP client and in-memory TTL cache."""
        self.http_client = http_client
        self.settings = settings
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}

    async def _request(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        """Run one HTTP GET request with timeout and retries."""
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.settings.HTTP_MAX_RETRIES),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        ):
            with attempt:
                response = await self.http_client.get(url, params=params, timeout=self.settings.WEATHER_TIMEOUT_SECONDS)
                response.raise_for_status()
                return response.json()
        raise RuntimeError("Weather request did not return a response.")

    async def get_destination_weather(self, destination: str) -> dict[str, Any]:
        """Resolve a destination and return a compact weather summary."""
        cached = self._cache.get(destination.lower())
        now = time.time()
        if cached and now - cached[0] < self.settings.WEATHER_CACHE_TTL_SECONDS:
            return cached[1]

        geocode_data = await self._request(
            self.settings.WEATHER_GEOCODING_URL,
            {"name": destination, "count": 1, "language": "en", "format": "json"},
        )
        results = geocode_data.get("results", [])
        if not results:
            raise ValueError(f"Could not geocode destination: {destination}")

        match = results[0]

        # --------- sending the request
        weather_data = await self._request(
            self.settings.WEATHER_FORECAST_URL,
            {
                "latitude": match["latitude"],
                "longitude": match["longitude"],
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "hourly": "precipitation_probability",
                "forecast_days": 1,
                "timezone": "auto",
            },
        )

        current = weather_data.get("current", {})
        precipitation_values = weather_data.get("hourly", {}).get("precipitation_probability", [])
        precipitation_probability = max(precipitation_values[:6], default=None)
        weather_code = current.get("weather_code")

        result = {
            "destination": destination,
            "resolved_name": match.get("name"),
            "country": match.get("country"),
            "temperature_c": current.get("temperature_2m"),
            "weather_summary": WEATHER_CODE_SUMMARIES.get(weather_code, "mixed conditions"),
            "precipitation_probability": precipitation_probability,
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "travel_note": self._build_travel_note(weather_code, precipitation_probability),
        }
        self._cache[destination.lower()] = (now, result)
        return result

    @staticmethod
    def _build_travel_note(weather_code: int | None, precipitation_probability: float | None) -> str:
        """Translate weather numbers into a short travel-friendly note."""
        if weather_code in {63, 65, 80, 95} or (precipitation_probability and precipitation_probability >= 60):
            return "Expect rain-related disruption for outdoor plans."
        if weather_code in {0, 1, 2}:
            return "Conditions look friendly for sightseeing and outdoor plans."
        return "Conditions are workable, but travelers should check local forecasts again before booking."
