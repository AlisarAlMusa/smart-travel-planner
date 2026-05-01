"""FastAPI app factory, lifespan hooks, and shared service singletons."""

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.graph import TravelAgentGraph
from app.api.routes import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import Base, SessionLocal, engine
from app.schemas.agent import HealthResponse
from app.services.azure_openai import build_async_azure_openai_client, build_azure_openai_client
from app.services.llm_service import LLMService
from app.services.ml_service import MLService
from app.services.rag_service import RAGService
from app.services.weather_service import WeatherService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load expensive clients once and close async resources on shutdown."""
    settings = get_settings()
    configure_logging()
    Base.metadata.create_all(bind=engine)

    async_http_client = httpx.AsyncClient()
    async_openai_client = build_async_azure_openai_client()
    sync_openai_client = build_azure_openai_client()

    llm_service = LLMService(async_openai_client, settings)
    ml_service = MLService(settings)
    weather_service = WeatherService(async_http_client, settings)
    rag_service = RAGService(
        SessionLocal,
        sync_openai_client,
        settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    )
    agent_graph = TravelAgentGraph(llm_service, rag_service, ml_service, weather_service)

    app.state.settings = settings
    app.state.http_client = async_http_client
    app.state.llm_service = llm_service
    app.state.ml_service = ml_service
    app.state.weather_service = weather_service
    app.state.rag_service = rag_service
    app.state.agent_graph = agent_graph

    try:
        yield
    finally:
        await async_http_client.aclose()


def create_app() -> FastAPI:
    """Build the FastAPI application with routes and shared lifespan state."""
    app = FastAPI(title="Travel Destination Backend", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        """Return a lightweight health response for deployment checks."""
        return HealthResponse()

    app.include_router(api_router)
    return app
