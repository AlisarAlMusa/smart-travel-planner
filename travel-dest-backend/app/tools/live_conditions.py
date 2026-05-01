"""Tool for fetching live weather conditions for candidate destinations."""

from pydantic import ValidationError

from app.schemas.tools import (
    DestinationWeather,
    GetLiveConditionsInput,
    GetLiveConditionsOutput,
    ToolError,
)
from app.services.weather_service import WeatherService


async def get_live_conditions(
    raw_input: dict,
    weather_service: WeatherService,
) -> GetLiveConditionsOutput:
    """Validate weather input, fetch live conditions, and return graceful partial failures."""
    try:
        validated_input = GetLiveConditionsInput.model_validate(raw_input)
    except ValidationError as exc:
        return GetLiveConditionsOutput(
            status="error",
            error=ToolError(
                error_type="validation_error",
                message="Invalid get_live_conditions arguments.",
                details={"errors": exc.errors()},
            ),
        )

    conditions: list[DestinationWeather] = []
    failures: list[str] = []

    for item in validated_input.destinations:
        try:
            weather_payload = await weather_service.get_destination_weather(item.destination)
            conditions.append(DestinationWeather(**weather_payload))
        except Exception as exc:
            failures.append(f"{item.destination}: {exc}")

    if conditions and failures:
        return GetLiveConditionsOutput(
            status="partial_success",
            conditions=conditions,
            error=ToolError(
                error_type="partial_failure",
                message="Some destinations could not be resolved.",
                details={"failures": failures},
            ),
        )

    if not conditions:
        return GetLiveConditionsOutput(
            status="error",
            error=ToolError(
                error_type="weather_lookup_failed",
                message="No live conditions could be fetched.",
                details={"failures": failures},
            ),
        )

    return GetLiveConditionsOutput(status="success", conditions=conditions)

