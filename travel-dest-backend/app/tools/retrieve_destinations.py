"""Tool for retrieving similar destinations from the pgvector RAG store."""

from typing import Any

from app.agent.prompts import (
    RETRIEVAL_REWRITE_SYSTEM_PROMPT,
    build_retrieval_rewrite_user_prompt,
)
from app.schemas.tools import (
    RetrievedDestination,
    RetrieveDestinationsInput,
    RetrieveDestinationsOutput,
    ToolError,
)
from app.services.llm_service import LLMService
from pydantic import ValidationError


async def retrieve_destinations(
    raw_input: dict,
    rag_service: Any,
    llm_service: LLMService,
) -> tuple[RetrieveDestinationsOutput, int, float]:
    """Validate retrieval input, rewrite the query, and fetch similar destinations."""
    try:
        validated_input = RetrieveDestinationsInput.model_validate(raw_input)
    except ValidationError as exc:
        return (
            RetrieveDestinationsOutput(
                status="error",
                error=ToolError(
                    error_type="validation_error",
                    message="Invalid retrieve_destinations arguments.",
                    details={"errors": exc.errors()},
                ),
            ),
            0,
            0.0,
        )

    # First the LLM rewrites the query, then we validate that output before retrieval.
    rewrite_result = await llm_service.generate_json(
        system_prompt=RETRIEVAL_REWRITE_SYSTEM_PROMPT,
        user_prompt=build_retrieval_rewrite_user_prompt(
            query=validated_input.query,
            style_hint=validated_input.style_hint,
            top_k=validated_input.top_k,
        ),
    )
    rewrite_payload = rewrite_result.parsed_json or {}

    try:
        cleaned_input = RetrieveDestinationsInput.model_validate(
            {
                "query": rewrite_payload.get("query", validated_input.query),
                "top_k": rewrite_payload.get("top_k", validated_input.top_k),
            }
        )
        query_embedding = await rag_service.embed_query(cleaned_input.query)
        results = rag_service.retrieve_similar_destinations(
            query_embedding=query_embedding,
            top_k=cleaned_input.top_k,
        )
        return (
            RetrieveDestinationsOutput(
                status="success",
                rewritten_query=cleaned_input.query,
                style_hint_used=validated_input.style_hint,
                destinations=[RetrievedDestination(**item) for item in results],
            ),
            rewrite_result.total_tokens,
            llm_service.estimate_cost(
                rewrite_result.prompt_tokens,
                rewrite_result.completion_tokens,
                strong=False,
            ),
        )
    except ValidationError as exc:
        return (
            RetrieveDestinationsOutput(
                status="error",
                error=ToolError(
                    error_type="validation_error",
                    message="The retrieval cleanup model returned invalid arguments.",
                    details={"errors": exc.errors()},
                ),
            ),
            rewrite_result.total_tokens,
            llm_service.estimate_cost(
                rewrite_result.prompt_tokens,
                rewrite_result.completion_tokens,
                strong=False,
            ),
        )
    except Exception as exc:
        return (
            RetrieveDestinationsOutput(
                status="error",
                error=ToolError(
                    error_type=type(exc).__name__,
                    message="Destination retrieval failed.",
                    details={"error": str(exc)},
                ),
            ),
            rewrite_result.total_tokens,
            llm_service.estimate_cost(
                rewrite_result.prompt_tokens,
                rewrite_result.completion_tokens,
                strong=False,
            ),
        )
