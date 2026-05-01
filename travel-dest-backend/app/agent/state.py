"""State object carried through the LangGraph workflow."""

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """Minimal state for the smart travel planner graph."""

    user_query: str
    user_id: str
    agent_run_id: str
    retrieval_result: dict[str, Any]
    trip_style_prediction: dict[str, Any]
    live_conditions_result: dict[str, Any]
    final_answer: str
    total_tokens: int
    estimated_cost: float
    tool_logs: list[dict[str, Any]]
