"""Tests for loading settings from environment variables."""

import pytest
from app.core.config import Settings
from pydantic import ValidationError


def set_required_settings(monkeypatch) -> None:
    """Set the required environment variables used by Settings."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://alisaralmusa:post334gres@localhost:5433/dests_db",
    )
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    monkeypatch.setenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
    monkeypatch.setenv("AZURE_OPENAI_CHEAP_DEPLOYMENT", "cheap-model")
    monkeypatch.setenv("AZURE_OPENAI_STRONG_DEPLOYMENT", "strong-model")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")


def test_settings_load_from_environment(monkeypatch) -> None:
    """The settings object should read values from environment variables."""
    set_required_settings(monkeypatch)
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-langsmith-key")

    settings = Settings()  # type: ignore[call-arg]

    assert settings.DATABASE_URL.endswith("dests_db")
    assert settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT == "text-embedding-3-small"
    assert settings.LANGSMITH_TRACING is True
    assert settings.LANGSMITH_API_KEY == "test-langsmith-key"
    assert settings.RAW_DATA_DIR == "data/raw"
    assert settings.WIKIVOYAGE_API_URL == "https://en.wikivoyage.org/w/api.php"


def test_settings_reject_missing_required_env(monkeypatch) -> None:
    """A required blank setting should produce a clear error message."""
    set_required_settings(monkeypatch)
    monkeypatch.setenv("AZURE_OPENAI_STRONG_DEPLOYMENT", "")

    with pytest.raises(ValidationError) as exc_info:
        Settings()  # type: ignore[call-arg]

    assert "AZURE_OPENAI_STRONG_DEPLOYMENT must be set" in str(exc_info.value)


def test_settings_reject_placeholder_values(monkeypatch) -> None:
    """Template placeholder values should not be accepted as real configuration."""
    set_required_settings(monkeypatch)
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "your_azure_openai_key")

    with pytest.raises(ValidationError) as exc_info:
        Settings()  # type: ignore[call-arg]

    assert "AZURE_OPENAI_API_KEY still has a placeholder value" in str(exc_info.value)
