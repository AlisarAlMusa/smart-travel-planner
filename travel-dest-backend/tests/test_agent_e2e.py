"""End-to-end graph test with mocked services."""

import pytest

pytest.importorskip("langgraph")

from app.agent.graph import TravelAgentGraph


class FakeLLMResult:
    """Fake LLM result object for orchestration tests."""

    def __init__(
        self,
        parsed_json=None,
        content: str = "",
        prompt_tokens: int = 12,
        completion_tokens: int = 6,
    ):
        self.parsed_json = parsed_json
        self.content = content
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

    @property
    def total_tokens(self) -> int:
        """Return total tokens."""
        return self.prompt_tokens + self.completion_tokens


class FakeLLMService:
    """Fake LLM service that covers rewrite, feature extraction, and synthesis."""

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        use_strong_model: bool = False,
    ):
        if "Top K" in user_prompt:
            return FakeLLMResult(parsed_json={"query": "sunny culture and food", "top_k": 2})
        return FakeLLMResult(
            parsed_json={
                "avg cost (usd/day)": 240,
                "avg_temp_year": 22,
                "hiking_score": 4,
                "beach_score": 8,
                "nightlife_score": 6,
                "culture_score": 8,
                "food_score": 9,
                "adventure_score": 5,
                "nature_score": 6,
                "safety_score": 7,
                "accommodation_type": "Boutique Hotel",
                "terrain_type": "Coastal",
            }
        )

    async def generate_text(self, system_prompt: str, user_prompt: str):
        return FakeLLMResult(
            content="Portugal looks strongest overall, but Thailand is a good fallback."
        )

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, strong: bool) -> float:
        return 0.002 if strong else 0.001


class FakeClassificationFailureLLMService(FakeLLMService):
    """Fake LLM service that makes classification feature validation fail."""

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        use_strong_model: bool = False,
    ):
        if "Top K" in user_prompt:
            return FakeLLMResult(parsed_json={"query": "sunny culture and food", "top_k": 2})
        return FakeLLMResult(parsed_json={"unexpected": "shape"})


class FakeRAGService:
    """Fake retrieval service for graph tests."""

    async def embed_query(self, query: str) -> list[float]:
        return [0.3, 0.2, 0.1]

    def retrieve_similar_destinations(self, query_embedding: list[float], top_k: int):
        return [
            {
                "destination": "Portugal",
                "title": "Portugal",
                "url": "https://example.com/portugal",
                "chunk_index": 0,
                "chunk_text": "Portugal offers beaches, food, and relaxed coastal cities.",
                "similarity_score": 0.9,
            },
            {
                "destination": "Thailand",
                "title": "Thailand",
                "url": "https://example.com/thailand",
                "chunk_index": 1,
                "chunk_text": "Thailand mixes beach escapes, food, and nightlife.",
                "similarity_score": 0.87,
            },
        ][:top_k]


class FakePrediction:
    """Fake prediction output for the ML service."""

    def __init__(self, predicted_style: str, confidence: float, features: dict):
        self.predicted_style = predicted_style
        self.confidence = confidence
        self.features = features


class FakeMLService:
    """Fake ML service for graph tests."""

    def predict_style(self, feature_payload: dict):
        return FakePrediction("Culture", 0.76, feature_payload)


class FakeWeatherService:
    """Fake weather service for graph tests."""

    async def get_destination_weather(self, destination: str):
        return {
            "destination": destination,
            "resolved_name": destination,
            "country": "Test Country",
            "temperature_c": 25,
            "weather_summary": "partly cloudy",
            "precipitation_probability": 30,
            "wind_speed_kmh": 14,
            "travel_note": (
                "Conditions are workable, but travelers should check local "
                "forecasts again before booking."
            ),
        }


@pytest.mark.anyio
async def test_agent_graph_end_to_end() -> None:
    """The graph should classify the user request first, then retrieve, then check weather."""
    graph = TravelAgentGraph(
        llm_service=FakeLLMService(),
        rag_service=FakeRAGService(),
        ml_service=FakeMLService(),
        weather_service=FakeWeatherService(),
    )
    result = await graph.run("I want warm food-focused destinations with culture")
    assert "Portugal" in result["final_answer"]
    assert result["trip_style_prediction"]["prediction"]["predicted_style"] == "Culture"
    assert len(result["retrieval_result"]["destinations"]) == 2
    assert result["live_conditions_result"]["conditions"][0]["destination"] == "Portugal"


@pytest.mark.anyio
async def test_agent_graph_continues_when_classification_fails() -> None:
    """The graph should keep retrieving when classification returns no prediction."""
    graph = TravelAgentGraph(
        llm_service=FakeClassificationFailureLLMService(),
        rag_service=FakeRAGService(),
        ml_service=FakeMLService(),
        weather_service=FakeWeatherService(),
    )
    result = await graph.run("I want warm food-focused destinations with culture")

    assert result["trip_style_prediction"]["status"] == "error"
    assert result["retrieval_result"]["destinations"][0]["destination"] == "Portugal"
    assert result["tool_logs"][1]["tool_input"]["style_hint"] is None
    assert "Portugal" in result["final_answer"]
