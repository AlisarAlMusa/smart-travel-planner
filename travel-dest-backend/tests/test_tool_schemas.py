"""Schema tests for the three required agent tools."""

import pytest
from pydantic import ValidationError

from app.schemas.tools import ClassifyTravelStyleInput, GetLiveConditionsInput, RetrieveDestinationsInput


def test_retrieve_schema_accepts_valid_payload() -> None:
    """The retrieval input should validate simple query payloads."""
    payload = RetrieveDestinationsInput.model_validate({"query": "warm beach city", "top_k": 3})
    assert payload.top_k == 3


def test_retrieve_schema_rejects_short_query() -> None:
    """A too-short retrieval query should raise a validation error."""
    with pytest.raises(ValidationError):
        RetrieveDestinationsInput.model_validate({"query": "hi", "top_k": 3})


def test_classify_schema_requires_destinations() -> None:
    """Classification now needs the user's trip request text."""
    with pytest.raises(ValidationError):
        ClassifyTravelStyleInput.model_validate({})


def test_live_conditions_schema_requires_one_destination() -> None:
    """Live conditions lookup should reject empty destination lists."""
    with pytest.raises(ValidationError):
        GetLiveConditionsInput.model_validate({"destinations": []})
