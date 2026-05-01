"""History routes for listing agent runs belonging to the current user."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import crud
from app.db.models import User
from app.api.dependencies import get_current_user, get_db
from app.schemas.agent import AgentRunHistoryItem


router = APIRouter()


@router.get("", response_model=list[AgentRunHistoryItem])
def list_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AgentRunHistoryItem]:
    """Return the authenticated user's previous agent runs."""
    runs = crud.list_agent_runs_for_user(db, current_user.id)
    return [AgentRunHistoryItem.model_validate(run) for run in runs]
