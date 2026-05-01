"""Shared Azure OpenAI client builders for chat and embeddings."""

from functools import lru_cache

from openai import AsyncAzureOpenAI, AzureOpenAI

from app.core.config import get_settings


@lru_cache(maxsize=1)
def build_azure_openai_client() -> AzureOpenAI:
    """Create and cache the synchronous Azure OpenAI client."""
    settings = get_settings()
    return AzureOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        timeout=settings.AZURE_OPENAI_TIMEOUT_SECONDS,
    )


@lru_cache(maxsize=1)
def build_async_azure_openai_client() -> AsyncAzureOpenAI:
    """Create and cache the asynchronous Azure OpenAI client."""
    settings = get_settings()
    return AsyncAzureOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        timeout=settings.AZURE_OPENAI_TIMEOUT_SECONDS,
    )

