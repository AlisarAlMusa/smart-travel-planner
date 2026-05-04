"""Tool that extracts ML features with the cheap model and predicts travel style with sklearn."""
# 1- LLm extracts ML features.
# 2- ML predictions.
from app.agent.prompts import (
    FEATURE_EXTRACTION_SYSTEM_PROMPT,
    build_feature_extraction_user_prompt,
)
from app.core.logging import get_logger
from app.schemas.tools import (
    ClassifyTravelStyleInput,
    ClassifyTravelStyleOutput,
    ExtractedDestinationFeatures,
    ToolError,
    TravelStylePrediction,
)
from app.services.llm_service import LLMService
from app.services.ml_service import MLService
from pydantic import ValidationError

logger = get_logger(__name__)


async def classify_travel_style(
    raw_input: dict,
    llm_service: LLMService,
    ml_service: MLService,
) -> tuple[ClassifyTravelStyleOutput, int, float]:
    """Validate the user request, extract ML features, and classify the requested trip style."""
    try:
        validated_input = ClassifyTravelStyleInput.model_validate(raw_input)
    except ValidationError as exc:
        logger.warning(
            "classify_travel_style received invalid input",
            extra={
                "event": "classify_travel_style_validation_error",
                "errors": exc.errors(),
            },
        )
        return (
            ClassifyTravelStyleOutput(
                status="error",
                error=ToolError(
                    error_type="validation_error",
                    message="Invalid classify_travel_style arguments.",
                    details={"errors": exc.errors()},
                ),
            ),
            0,
            0.0,
        )

    extraction = None
    try:
        logger.info(
            "Extracting travel-style ML features",
            extra={"event": "classify_travel_style_feature_extraction_start"},
        )
        # ---------- 1
        extraction = await llm_service.generate_json(
            system_prompt=FEATURE_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=build_feature_extraction_user_prompt(validated_input.user_query),
        )
        logger.info(
            "Received extracted travel-style features",
            extra={
                "event": "classify_travel_style_feature_extraction_finish",
                "parsed_json": extraction.parsed_json,
                "prompt_tokens": extraction.prompt_tokens,
                "completion_tokens": extraction.completion_tokens,
            },
        )
        feature_model = ExtractedDestinationFeatures.model_validate(extraction.parsed_json or {})
        logger.info(
            "Validated extracted travel-style features",
            extra={
                "event": "classify_travel_style_feature_validation_success",
                "feature_payload": feature_model.to_model_payload(),
            },
        )
        # ---------- 2
        prediction = ml_service.predict_style(feature_model.to_model_payload())
        logger.info(
            "Predicted travel style",
            extra={
                "event": "classify_travel_style_prediction_success",
                "predicted_style": prediction.predicted_style,
                "confidence": prediction.confidence,
            },
        )
        output = ClassifyTravelStyleOutput(
            status="success",
            prediction=TravelStylePrediction(
                user_query=validated_input.user_query,
                predicted_style=prediction.predicted_style,
                confidence=prediction.confidence,
                extracted_features=prediction.features,
            ),
        )
        # -------- 3
        total_tokens = extraction.prompt_tokens + extraction.completion_tokens
        cost = llm_service.estimate_cost(
            extraction.prompt_tokens,
            extraction.completion_tokens,
            strong=False,
        )
        return output, total_tokens, cost
    except Exception as exc:
        total_prompt_tokens = extraction.prompt_tokens if extraction is not None else 0
        total_completion_tokens = extraction.completion_tokens if extraction is not None else 0
        logger.exception(
            "Failed to classify travel style",
            extra={
                "event": "classify_travel_style_error",
                "error_type": type(exc).__name__,
                "parsed_json": extraction.parsed_json if extraction is not None else None,
                "raw_content": extraction.content if extraction is not None else None,
            },
        )
        return (
            ClassifyTravelStyleOutput(
                status="error",
                error=ToolError(
                    error_type=type(exc).__name__,
                    message="Failed to classify the user's requested travel style.",
                    details={"user_query": validated_input.user_query, "error": str(exc)},
                ),
            ),
            total_prompt_tokens + total_completion_tokens,
            llm_service.estimate_cost(total_prompt_tokens, total_completion_tokens, strong=False),
        )
