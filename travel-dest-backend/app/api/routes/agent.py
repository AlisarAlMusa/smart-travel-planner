"""Agent route for running the smart travel planner end to end."""
# all dependecies are injected via FastAPI Depends
# uses Async
# create w new agent_run in the db 
# uses langsmith tracing context to capture all tool calls and the final answer

from fastapi import APIRouter, Depends
from langsmith import tracing_context
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.logging import get_logger
from app.db import crud
from app.db.models import User
from app.api.dependencies import get_agent_graph, get_app_settings, get_current_user, get_db
from app.schemas.agent import AgentRunRequest, AgentRunResponse


logger = get_logger(__name__)
router = APIRouter()


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    payload: AgentRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    agent_graph=Depends(get_agent_graph),
) -> AgentRunResponse:
    """Run the smart travel planner for one authenticated user."""
    agent_run = crud.create_agent_run(db, current_user.id, payload.query)

    with tracing_context(enabled=settings.LANGSMITH_TRACING):
        state = await agent_graph.run(payload.query)

    retrieval_result = state["retrieval_result"]
    trip_style_prediction_result = state["trip_style_prediction"]
    live_conditions_result = state["live_conditions_result"]

    for tool_log in state.get("tool_logs", []):
        crud.create_tool_call(
            db=db,
            agent_run_id=agent_run.id,
            tool_name=tool_log["tool_name"],
            tool_input=tool_log["tool_input"],
            tool_output=tool_log["output"],
            status=tool_log["status"],
            latency_ms=tool_log["latency_ms"],
            error_message=tool_log["error_message"],
        )

    crud.update_agent_run_result(
        db=db,
        agent_run=agent_run,
        final_answer=state["final_answer"],
        total_tokens=state["total_tokens"],
        estimated_cost=state["estimated_cost"],
    )
    logger.info(
        "Completed agent run",
        extra={
            "event": "agent_run",
            "agent_run_id": str(agent_run.id),
            "user_id": str(current_user.id),
            "total_tokens": state["total_tokens"],
            "estimated_cost": state["estimated_cost"],
            "status": "success",
        },
    )
    return AgentRunResponse(
        agent_run_id=agent_run.id,
        final_answer=state["final_answer"],
        total_tokens=state["total_tokens"],
        estimated_cost=state["estimated_cost"],
        retrieval=retrieval_result,
        trip_style_prediction=trip_style_prediction_result,
        live_conditions=live_conditions_result,
        tool_calls=state.get("tool_logs", []),
    )
