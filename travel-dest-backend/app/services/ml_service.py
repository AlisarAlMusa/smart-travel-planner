"""Load the trained ML artifact once and provide travel-style predictions."""

from dataclasses import dataclass
from typing import Any

import joblib
import pandas as pd

from app.core.config import Settings


@dataclass
class MLPrediction:
    """One ML prediction plus confidence and feature payload."""

    predicted_style: str
    confidence: float
    features: dict[str, Any]


class MLService:
    """Wrap the trained sklearn pipeline used for travel-style classification."""

    def __init__(self, settings: Settings) -> None:
        """Load the saved pipeline once during application startup."""
        artifact = joblib.load(settings.model_artifact_full_path)
        self.pipeline = artifact["pipeline"]
        self.class_names = artifact["class_names"]
        self.feature_columns = artifact["feature_columns"]

    def predict_style(self, feature_payload: dict[str, Any]) -> MLPrediction:
        """Predict a travel style from fully prepared ML features."""
        frame = pd.DataFrame([feature_payload], columns=self.feature_columns)
        prediction = self.pipeline.predict(frame)[0]
        probabilities = self.pipeline.predict_proba(frame)[0]
        confidence = float(max(probabilities))
        return MLPrediction(
            predicted_style=str(prediction),
            confidence=confidence,
            features=feature_payload,
        )

