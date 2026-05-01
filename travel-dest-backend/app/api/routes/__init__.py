"""Aggregate API routers for the backend application."""

from fastapi import APIRouter

from app.api.routes.agent import router as agent_router
from app.api.routes.auth import router as auth_router
from app.api.routes.history import router as history_router


api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(agent_router, prefix="/agent", tags=["agent"])
api_router.include_router(history_router, prefix="/history", tags=["history"])

