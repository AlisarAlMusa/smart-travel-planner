"""Isolated tests for the three required agent tools."""

import pytest

from app.tools.classify_travel_style import classify_travel_style
from app.tools.live_conditions import get_live_conditions
from app.tools.retrieve_destinations import retrieve_destinations


class FakeLLMResult:
    """Simple fake LLM result object used in tests."""

    def __init__(self, parsed_json=None, content: str = "", prompt_tokens: int = 10, completion_tokens: int = 5):
        self.parsed_json = parsed_json
        self.content = content
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

    @property
    def total_tokens(self) -> int:
        """Return combined token usage."""
        return self.prompt_tokens + self.completion_tokens


class FakeLLMService:
    """Fake LLM service for query rewriting and feature extraction."""

    async def generate_json(self, system_prompt: str, user_prompt: str, use_strong_model: bool = False):
        if "Top K" in user_prompt:
            return FakeLLMResult(parsed_json={"query": "relaxing beaches and food", "top_k": 2})
        return FakeLLMResult(
            parsed_json={
                "avg cost (usd/day)": 210,
                "avg_temp_year": 24,
                "hiking_score": 4,
                "beach_score": 9,
                "nightlife_score": 7,
                "culture_score": 6,
                "food_score": 8,
                "adventure_score": 5,
                "nature_score": 7,
                "safety_score": 7,
                "accommodation_type": "Resort",
                "terrain_type": "Coastal",
            }
        )

    async def generate_text(self, system_prompt: str, user_prompt: str):
        return FakeLLMResult(content="Portugal is the best match overall.")

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, strong: bool) -> float:
        return 0.001


class FakeRAGService:
    """Fake RAG service that returns a fixed destination list."""

    async def embed_query(self, query: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def retrieve_similar_destinations(self, query_embedding: list[float], top_k: int):
        return [
            {
                "destination": "Portugal",
                "title": "Portugal",
                "url": "https://example.com/portugal",
                "chunk_index": 0,
                "chunk_text": "Portugal offers beaches, food, relaxed pacing, and sunny coastal trips.",
                "similarity_score": 0.92,
            },
            {
                "destination": "Thailand",
                "title": "Thailand",
                "url": "https://example.com/thailand",
                "chunk_index": 1,
                "chunk_text": "Thailand mixes beaches, nightlife, island trips, and affordable options.",
                "similarity_score": 0.88,
            },
        ][:top_k]


class FakePrediction:
    """Fake ML prediction object."""

    def __init__(self, predicted_style: str, confidence: float, features: dict):
        self.predicted_style = predicted_style
        self.confidence = confidence
        self.features = features


class FakeMLService:
    """Fake ML service that returns a stable style prediction."""

    def predict_style(self, feature_payload: dict):
        return FakePrediction("Relaxation", 0.81, feature_payload)


class FakeWeatherService:
    """Fake weather service that returns a stable condition payload."""

    async def get_destination_weather(self, destination: str):
        return {
            "destination": destination,
            "resolved_name": destination,
            "country": "Test Country",
            "temperature_c": 27,
            "weather_summary": "clear skies",
            "precipitation_probability": 10,
            "wind_speed_kmh": 12,
            "travel_note": "Conditions look friendly for sightseeing and outdoor plans.",
        }


@pytest.mark.anyio
async def test_retrieve_destinations_tool() -> None:
    """The retrieval tool should return validated destination matches."""
    output, tokens, cost = await retrieve_destinations(
        {"query": "I want sunny beaches and great food", "top_k": 2, "style_hint": "Relaxation"},
        rag_service=FakeRAGService(),
        llm_service=FakeLLMService(),
    )
    assert output.status == "success"
    assert len(output.destinations) == 2
    assert output.style_hint_used == "Relaxation"
    assert tokens > 0
    assert cost >= 0


@pytest.mark.anyio
async def test_classify_travel_style_tool() -> None:
    """The classification tool should predict the style the user is asking for."""
    output, tokens, cost = await classify_travel_style(
        {"user_query": "I want beaches, seafood, and a slow-paced coastal trip."},
        llm_service=FakeLLMService(),
        ml_service=FakeMLService(),
    )
    assert output.status == "success"
    assert output.prediction is not None
    assert output.prediction.predicted_style == "Relaxation"
    assert tokens > 0
    assert cost >= 0


@pytest.mark.anyio
async def test_get_live_conditions_tool() -> None:
    """The live conditions tool should return weather for the requested destinations."""
    output = await get_live_conditions(
        {"destinations": [{"destination": "Portugal"}]},
        weather_service=FakeWeatherService(),
    )
    assert output.status == "success"
    assert output.conditions[0].weather_summary == "clear skies"
