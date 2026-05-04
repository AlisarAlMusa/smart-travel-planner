"""Application configuration shared by the API, agent, and ingestion scripts."""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
BACKEND_ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(BACKEND_ENV_FILE, override=False)

REQUIRED_ENV_FIELDS = (
    "DATABASE_URL",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_VERSION",
    "AZURE_OPENAI_CHEAP_DEPLOYMENT",
    "AZURE_OPENAI_STRONG_DEPLOYMENT",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    "JWT_SECRET_KEY",
)
PLACEHOLDER_VALUES = {
    "change-me",
    "change_this_secret",
    "your_azure_openai_key",
    "https://your-resource-name.openai.azure.com/",
}


class Settings(BaseSettings):
    """Load environment variables for the backend and agent stack."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        validate_default=True,
    )

    DATABASE_URL: str = ""

    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_VERSION: str = ""
    AZURE_OPENAI_CHEAP_DEPLOYMENT: str = ""
    AZURE_OPENAI_STRONG_DEPLOYMENT: str = ""
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = ""

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "travel-planner-agent"

    RAW_DATA_DIR: str = "data/raw"
    PROCESSED_DATA_DIR: str = "data/processed"
    CHUNKS_DATA_DIR: str = "data/chunks"

    CHUNK_TARGET_TOKENS: int = 2500
    CHUNK_OVERLAP_TOKENS: int = 150
    MAX_CHUNKS_PER_DESTINATION: int = 4

    WIKIVOYAGE_API_URL: str = "https://en.wikivoyage.org/w/api.php"
    WIKIVOYAGE_USER_AGENT: str = (
        "travel-dest-recommender/0.1 (educational project; contact: your-email@example.com)"
    )
    WIKIVOYAGE_TIMEOUT_SECONDS: int = 20

    WEATHER_GEOCODING_URL: str = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_FORECAST_URL: str = "https://api.open-meteo.com/v1/forecast"
    WEATHER_TIMEOUT_SECONDS: int = 20
    WEATHER_CACHE_TTL_SECONDS: int = 600

    AZURE_OPENAI_TIMEOUT_SECONDS: int = 30
    LLM_MAX_RETRIES: int = 3
    HTTP_MAX_RETRIES: int = 3
    AGENT_TOP_K_DESTINATIONS: int = 3
    EMBEDDING_DIMENSION: int = 1536
    EMBEDDING_MAX_INPUT_WORDS: int = 7000
    EMBEDDING_REQUEST_DELAY_SECONDS: float = 3.0
    MODEL_ARTIFACT_PATH: str = "artifacts/model.joblib"

    CHEAP_MODEL_INPUT_COST_PER_1K: float = Field(default=0.0)
    CHEAP_MODEL_OUTPUT_COST_PER_1K: float = Field(default=0.0)
    STRONG_MODEL_INPUT_COST_PER_1K: float = Field(default=0.0)
    STRONG_MODEL_OUTPUT_COST_PER_1K: float = Field(default=0.0)

    @field_validator(*REQUIRED_ENV_FIELDS)
    @classmethod
    def validate_required_env_value(cls, value: str, info: ValidationInfo) -> str:
        """Reject missing, blank, or template placeholder settings with a clear message."""
        field_name = info.field_name or "unknown setting"

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be set in travel-dest-backend/.env")

        cleaned_value = value.strip()
        if cleaned_value in PLACEHOLDER_VALUES:
            raise ValueError(
                f"{field_name} still has a placeholder value. "
                "Replace it in travel-dest-backend/.env before starting the backend."
            )

        return cleaned_value

    @property
    def base_dir(self) -> Path:
        """Return the backend directory."""
        return BACKEND_DIR

    @property
    def repo_root(self) -> Path:
        """Return the repository root so shared artifacts can be loaded."""
        return self.base_dir.parent

    @property
    def raw_data_path(self) -> Path:
        """Return the absolute raw data directory."""
        return self.base_dir / self.RAW_DATA_DIR

    @property
    def processed_data_path(self) -> Path:
        """Return the absolute processed data directory."""
        return self.base_dir / self.PROCESSED_DATA_DIR

    @property
    def chunks_data_path(self) -> Path:
        """Return the absolute chunk data directory."""
        return self.base_dir / self.CHUNKS_DATA_DIR

    @property
    def model_artifact_full_path(self) -> Path:
        """Return the full path to the trained ML artifact."""
        return self.repo_root / self.MODEL_ARTIFACT_PATH


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cache settings so all modules share one validated configuration object."""
    return Settings()  # type: ignore[call-arg]
