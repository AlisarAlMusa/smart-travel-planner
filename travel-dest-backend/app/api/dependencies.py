"""FastAPI dependencies for database access, auth, and shared services."""

from collections.abc import Generator
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.db import crud
from app.db.models import User
from app.db.session import get_db as session_get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db() -> Generator[Session, None, None]:
    """Expose the database session as an API-level dependency."""
    yield from session_get_db()


def get_app_settings() -> Settings:
    """Expose validated settings through dependency injection."""
    return get_settings()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> User:
    """Return the authenticated user for the current request."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials.",
    )

    try:
        payload = decode_access_token(token, settings)
        user_id = UUID(str(payload.get("sub")))
    except Exception as exc:  # pragma: no cover - simple auth boundary
        raise credentials_error from exc

    user = crud.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_error
    return user


def get_agent_graph(request: Request):
    """Return the compiled LangGraph travel planner from app state."""
    return request.app.state.agent_graph


def get_llm_service(request: Request):
    """Return the shared LLM service singleton."""
    return request.app.state.llm_service


def get_rag_service(request: Request):
    """Return the shared RAG service singleton."""
    return request.app.state.rag_service


def get_ml_service(request: Request):
    """Return the shared ML service singleton."""
    return request.app.state.ml_service


def get_weather_service(request: Request):
    """Return the shared weather service singleton."""
    return request.app.state.weather_service
