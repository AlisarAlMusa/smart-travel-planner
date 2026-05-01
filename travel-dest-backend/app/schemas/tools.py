"""Schemas for validated agent tool inputs and outputs."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolError(BaseModel):
    """Structured tool error returned to the agent when validation or execution fails."""

    error_type: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class RetrieveDestinationsInput(BaseModel):
    """Validated input for semantic destination retrieval."""

    query: str = Field(min_length=3)
    top_k: int = Field(default=3, ge=1, le=5)
    style_hint: str | None = None


class RetrievedDestination(BaseModel):
    """One retrieved destination chunk plus its similarity score."""

    destination: str
    title: str | None = None
    url: str | None = None
    chunk_index: int
    chunk_text: str
    similarity_score: float


class RetrieveDestinationsOutput(BaseModel):
    """Structured retrieval output returned to the orchestration layer."""

    status: Literal["success", "error"]
    rewritten_query: str | None = None
    style_hint_used: str | None = None
    destinations: list[RetrievedDestination] = Field(default_factory=list)
    error: ToolError | None = None


class UserTripRequestForClassification(BaseModel):
    """Input payload for ML classification from the user's trip request."""

    user_query: str = Field(min_length=5)


class ExtractedDestinationFeatures(BaseModel):
    """ML feature values inferred from destination text by the cheap model."""

    avg_cost_usd_per_day: float = Field(alias="avg cost (usd/day)", ge=0)
    avg_temp_year: float
    hiking_score: float = Field(ge=0, le=10)
    beach_score: float = Field(ge=0, le=10)
    nightlife_score: float = Field(ge=0, le=10)
    culture_score: float = Field(ge=0, le=10)
    food_score: float = Field(ge=0, le=10)
    adventure_score: float = Field(ge=0, le=10)
    nature_score: float = Field(ge=0, le=10)
    safety_score: float = Field(ge=0, le=10)
    accommodation_type: str
    terrain_type: str

    model_config = {"populate_by_name": True}

    def to_model_payload(self) -> dict[str, Any]:
        """Return the exact feature names expected by the trained pipeline."""
        return {
            "avg cost (usd/day)": self.avg_cost_usd_per_day,
            "avg_temp_year": self.avg_temp_year,
            "hiking_score": self.hiking_score,
            "beach_score": self.beach_score,
            "nightlife_score": self.nightlife_score,
            "culture_score": self.culture_score,
            "food_score": self.food_score,
            "adventure_score": self.adventure_score,
            "nature_score": self.nature_score,
            "safety_score": self.safety_score,
            "accommodation_type": self.accommodation_type,
            "terrain_type": self.terrain_type,
        }


class ClassifyTravelStyleInput(BaseModel):
    """Validated input for the ML classification tool."""

    user_query: str = Field(min_length=5)


class TravelStylePrediction(BaseModel):
    """The ML prediction for the travel style the user is asking for."""

    user_query: str
    predicted_style: str
    confidence: float
    extracted_features: dict[str, Any]


class ClassifyTravelStyleOutput(BaseModel):
    """Structured classification results returned to the agent."""

    status: Literal["success", "error"]
    prediction: TravelStylePrediction | None = None
    error: ToolError | None = None


class LiveConditionsRequestItem(BaseModel):
    """Location requested for live weather lookups."""

    destination: str


class GetLiveConditionsInput(BaseModel):
    """Validated input for the weather lookup tool."""

    destinations: list[LiveConditionsRequestItem] = Field(min_length=1, max_length=5)


class DestinationWeather(BaseModel):
    """Normalized weather snapshot for one destination."""

    destination: str
    resolved_name: str | None = None
    country: str | None = None
    temperature_c: float | None = None
    weather_summary: str | None = None
    precipitation_probability: float | None = None
    wind_speed_kmh: float | None = None
    travel_note: str | None = None


class GetLiveConditionsOutput(BaseModel):
    """Structured live condition results returned to the agent."""

    status: Literal["success", "partial_success", "error"]
    conditions: list[DestinationWeather] = Field(default_factory=list)
    error: ToolError | None = None
