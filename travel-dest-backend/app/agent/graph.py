"""LangGraph wrapper around the travel planner orchestration flow."""

from time import perf_counter
from typing import Any

from app.agent.prompts import FINAL_SYNTHESIS_SYSTEM_PROMPT, build_final_synthesis_user_prompt
from app.agent.state import AgentState
from app.agent.tool_registry import dispatch_tool
from app.core.logging import get_logger
from app.tools.classify_travel_style import classify_travel_style
from app.tools.live_conditions import get_live_conditions
from app.tools.retrieve_destinations import retrieve_destinations
from langgraph.graph import END, START, StateGraph

logger = get_logger(__name__)


class TravelAgentGraph:
    """Build and execute the simple LangGraph workflow for the smart travel planner."""

    def __init__(self, llm_service, rag_service, ml_service, weather_service) -> None:
        """Store shared services and compile the graph once."""
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.ml_service = ml_service
        self.weather_service = weather_service
        self.graph = self._build_graph()

    def _build_graph(self):
        """Compile the four-step graph: classify, retrieve, live conditions, synthesize."""
        graph = StateGraph(AgentState)
        graph.add_node("classify", self._classify_node)
        graph.add_node("retrieve", self._retrieve_node)
        graph.add_node("live_conditions", self._live_conditions_node)
        graph.add_node("synthesize", self._synthesize_node)

        graph.add_edge(START, "classify")
        graph.add_edge("classify", "retrieve")
        graph.add_edge("retrieve", "live_conditions")
        graph.add_edge("live_conditions", "synthesize")
        graph.add_edge("synthesize", END)
        return graph.compile()

    @staticmethod
    def _require_state_text(state: AgentState, key: str) -> str:
        """Return one required text value from state or raise a clear error."""
        value = state.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"Missing required state value: {key}")
        return value

    @staticmethod
    def _require_state_dict(state: AgentState, key: str) -> dict[str, Any]:
        """Return one required dictionary value from state or raise a clear error."""
        value = state.get(key)
        if not isinstance(value, dict):
            raise ValueError(f"Missing required state object: {key}")
        return value

    @staticmethod
    def _get_predicted_style(state: AgentState) -> str | None:
        """Return the predicted style when classification succeeded, otherwise None."""
        prediction_result = state.get("trip_style_prediction", {})
        if not isinstance(prediction_result, dict):
            return None

        prediction = prediction_result.get("prediction")
        if not isinstance(prediction, dict):
            return None

        predicted_style = prediction.get("predicted_style")
        return predicted_style if isinstance(predicted_style, str) else None

    async def _classify_node(self, state: AgentState) -> AgentState:
        """Classify the travel style implied by the user's trip request."""
        started_at = perf_counter()
        user_query = self._require_state_text(state, "user_query")
        tool_input = {"user_query": user_query}
        logger.info(
            "Starting classify_travel_style tool",
            extra={"event": "agent_tool_start", "tool_name": "classify_travel_style"},
        )
        result, tokens, cost = await dispatch_tool(
            "classify_travel_style",
            lambda: classify_travel_style(
                tool_input,
                llm_service=self.llm_service,
                ml_service=self.ml_service,
            ),
        )
        latency_ms = int((perf_counter() - started_at) * 1000)
        logger.info(
            "Finished classify_travel_style tool",
            extra={
                "event": "agent_tool_finish",
                "tool_name": "classify_travel_style",
                "status": result.status,
                "latency_ms": latency_ms,
                "predicted_style": (
                    result.prediction.predicted_style if result.prediction is not None else None
                ),
                "error_type": result.error.error_type if result.error else None,
                "error_message": result.error.message if result.error else None,
                "error_details": result.error.details if result.error else None,
            },
        )
        tool_logs = list(state.get("tool_logs", []))
        tool_logs.append(
            {
                "tool_name": "classify_travel_style",
                "status": result.status,
                "latency_ms": latency_ms,
                "tool_input": tool_input,
                "output": result.model_dump(),
                "error_message": result.error.message if result.error else None,
            }
        )
        return {
            "trip_style_prediction": result.model_dump(),
            "total_tokens": state.get("total_tokens", 0) + tokens,
            "estimated_cost": state.get("estimated_cost", 0.0) + cost,
            "tool_logs": tool_logs,
        }

    async def _retrieve_node(self, state: AgentState) -> AgentState:
        """Retrieve similar destinations using the user query plus predicted trip style."""
        started_at = perf_counter()
        user_query = self._require_state_text(state, "user_query")
        predicted_style = self._get_predicted_style(state)
        if predicted_style is None:
            logger.warning(
                "No predicted style available; retrieval will continue without a style hint",
                extra={
                    "event": "agent_missing_style_hint",
                    "classification_status": state.get("trip_style_prediction", {}).get("status")
                    if isinstance(state.get("trip_style_prediction"), dict)
                    else None,
                },
            )
        tool_input = {
            "query": user_query,
            "top_k": 3,
            "style_hint": predicted_style,
        }
        logger.info(
            "Starting retrieve_destinations tool",
            extra={
                "event": "agent_tool_start",
                "tool_name": "retrieve_destinations",
                "style_hint": predicted_style,
            },
        )
        result, tokens, cost = await dispatch_tool(
            "retrieve_destinations",
            lambda: retrieve_destinations(
                tool_input,
                rag_service=self.rag_service,
                llm_service=self.llm_service,
            ),
        )
        latency_ms = int((perf_counter() - started_at) * 1000)
        logger.info(
            "Finished retrieve_destinations tool",
            extra={
                "event": "agent_tool_finish",
                "tool_name": "retrieve_destinations",
                "status": result.status,
                "latency_ms": latency_ms,
                "destination_count": len(result.destinations),
                "error_type": result.error.error_type if result.error else None,
                "error_message": result.error.message if result.error else None,
            },
        )
        tool_logs = list(state.get("tool_logs", []))
        tool_logs.append(
            {
                "tool_name": "retrieve_destinations",
                "status": result.status,
                "latency_ms": latency_ms,
                "tool_input": tool_input,
                "output": result.model_dump(),
                "error_message": result.error.message if result.error else None,
            }
        )
        return {
            "retrieval_result": result.model_dump(),
            "total_tokens": state.get("total_tokens", 0) + tokens,
            "estimated_cost": state.get("estimated_cost", 0.0) + cost,
            "tool_logs": tool_logs,
        }

    async def _live_conditions_node(self, state: AgentState) -> AgentState:
        """Fetch live weather conditions for the retrieved destinations."""
        retrieval_result = self._require_state_dict(state, "retrieval_result")
        destinations = [
            {"destination": item["destination"]}
            for item in retrieval_result.get("destinations", [])
        ]
        started_at = perf_counter()
        tool_input = {"destinations": destinations}
        logger.info(
            "Starting get_live_conditions tool",
            extra={
                "event": "agent_tool_start",
                "tool_name": "get_live_conditions",
                "destination_count": len(destinations),
            },
        )
        result = await dispatch_tool(
            "get_live_conditions",
            lambda: get_live_conditions(tool_input, weather_service=self.weather_service),
        )
        latency_ms = int((perf_counter() - started_at) * 1000)
        logger.info(
            "Finished get_live_conditions tool",
            extra={
                "event": "agent_tool_finish",
                "tool_name": "get_live_conditions",
                "status": result.status,
                "latency_ms": latency_ms,
                "condition_count": len(result.conditions),
                "error_type": result.error.error_type if result.error else None,
                "error_message": result.error.message if result.error else None,
            },
        )
        tool_logs = list(state.get("tool_logs", []))
        tool_logs.append(
            {
                "tool_name": "get_live_conditions",
                "status": result.status,
                "latency_ms": latency_ms,
                "tool_input": tool_input,
                "output": result.model_dump(),
                "error_message": result.error.message if result.error else None,
            }
        )
        return {"live_conditions_result": result.model_dump(), "tool_logs": tool_logs}

    async def _synthesize_node(self, state: AgentState) -> AgentState:
        """Ask the strong model to combine retrieval, ML, and weather into one answer."""
        user_query = self._require_state_text(state, "user_query")
        retrieval_result = self._require_state_dict(state, "retrieval_result")
        trip_style_prediction = self._require_state_dict(state, "trip_style_prediction")
        live_conditions_result = self._require_state_dict(state, "live_conditions_result")
        synthesis_prompt = build_final_synthesis_user_prompt(
            user_query=user_query,
            retrieval_result=retrieval_result,
            trip_style_prediction=trip_style_prediction,
            live_conditions_result=live_conditions_result,
        )
        try:
            logger.info("Starting final synthesis", extra={"event": "agent_synthesis_start"})
            result = await self.llm_service.generate_text(
                system_prompt=FINAL_SYNTHESIS_SYSTEM_PROMPT,
                user_prompt=synthesis_prompt,
            )
            total_tokens = state.get("total_tokens", 0) + result.total_tokens
            total_cost = state.get("estimated_cost", 0.0) + self.llm_service.estimate_cost(
                result.prompt_tokens,
                result.completion_tokens,
                strong=True,
            )
            return {
                "final_answer": result.content,
                "total_tokens": total_tokens,
                "estimated_cost": total_cost,
            }
        except Exception:
            logger.exception("Final synthesis failed; using fallback answer")
            fallback_answer = self._build_fallback_answer(state)
            return {"final_answer": fallback_answer}

    @staticmethod
    def _build_fallback_answer(state: AgentState) -> str:
        """Build a plain fallback answer if the final strong-model call fails."""
        destinations = [
            item["destination"]
            for item in state.get("retrieval_result", {}).get("destinations", [])
        ]
        prediction = state.get("trip_style_prediction", {}).get("prediction")
        if prediction is None:
            prediction = state.get("trip_style_prediction", {}).get("error", {})
        weather = state.get("live_conditions_result", {}).get("conditions", [])
        return (
            "I could not complete the final synthesis step, but the strongest "
            "retrieved destinations were "
            f"{', '.join(destinations) or 'not available'}. "
            f"The ML-predicted requested travel style was: {prediction}. "
            f"Live conditions were: {weather}."
        )

    async def run(self, query: str) -> dict:
        """Execute the compiled graph and return the final state."""
        logger.info("Starting agent graph run", extra={"event": "agent_run_start"})
        return await self.graph.ainvoke(
            {
                "user_query": query,
                "total_tokens": 0,
                "estimated_cost": 0.0,
                "tool_logs": [],
            }
        )
