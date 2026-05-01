"""Schemas for the agent route, response payloads, and internal summaries."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.tools import (
    ClassifyTravelStyleOutput,
    GetLiveConditionsOutput,
    RetrieveDestinationsOutput,
)


class HealthResponse(BaseModel):
    """Small health response for quick checks."""

    status: str = "ok"


class AgentRunRequest(BaseModel):
    """Incoming user query for the smart travel planner agent."""

    query: str = Field(min_length=5)


class ToolCallLogResponse(BaseModel):
    """Tool call payload returned in agent responses and history."""

    tool_name: str
    status: str
    latency_ms: int
    tool_input: dict[str, Any] | None = None
    output: dict[str, Any]
    error_message: str | None = None


class AgentRunResponse(BaseModel):
    """Full response from one agent execution."""

    agent_run_id: UUID
    final_answer: str
    total_tokens: int
    estimated_cost: float
    retrieval: RetrieveDestinationsOutput
    trip_style_prediction: ClassifyTravelStyleOutput
    live_conditions: GetLiveConditionsOutput
    tool_calls: list[ToolCallLogResponse]


class AgentRunHistoryItem(BaseModel):
    """One persisted agent run shown in user history."""

    id: UUID
    user_query: str
    final_answer: str | None = None
    total_tokens: int
    estimated_cost: float
    created_at: datetime

    model_config = {"from_attributes": True}
