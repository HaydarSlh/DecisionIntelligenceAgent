# ============================================================
# ML Model — loads the trained priority classifier and predicts
# ============================================================
# The pipeline (TF-IDF + StandardScaler + LightGBM) is saved
# as a joblib artifact by the notebook. This module loads it
# once at startup and exposes a single predict_priority() call.
# ============================================================

import json
import logging
import time
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.config import MODEL_PATH, THRESHOLD_PATH
from app.feature_extractor import NUMERIC_FEATURE_COLS, extract_numeric_features

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_artifacts() -> tuple:
    """Load pipeline + threshold once; cached for the lifetime of the process."""
    model_path = Path(MODEL_PATH)
    if not model_path.exists():
        logger.warning("ML model not found at %s — priority/ml will return unavailable", model_path)
        return None, 0.5

    import joblib
    pipe = joblib.load(model_path)

    threshold = 0.5
    thr_path = Path(THRESHOLD_PATH)
    if thr_path.exists():
        with open(thr_path) as f:
            threshold = json.load(f).get("threshold", 0.5)

    logger.info("ML model loaded | path=%s threshold=%.3f", model_path, threshold)
    return pipe, threshold


def predict_priority(text: str) -> dict:
    """Predict urgency for a single support ticket text.

    Returns:
        label: "urgent" or "normal" (or "unavailable" if model not loaded)
        confidence: P(urgent) float 0–1
        latency_ms: wall-clock time for this call
        model_available: whether the joblib artifact was found
    """
    t0 = time.perf_counter()

    pipe, threshold = _load_artifacts()

    if pipe is None:
        return {
            "label": "unavailable",
            "confidence": 0.0,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            "model_available": False,
        }

    # Build the same DataFrame the Pipeline.predict_proba() expects:
    # one row with 'text' column + all NUMERIC_FEATURE_COLS
    num_feats = extract_numeric_features([text])
    row = {"text": [text]}
    for col in NUMERIC_FEATURE_COLS:
        row[col] = num_feats[col].values
    df = pd.DataFrame(row)

    proba = float(pipe.predict_proba(df)[0][1])  # P(urgent)
    label = "urgent" if proba >= threshold else "normal"
    confidence = round(proba if label == "urgent" else 1.0 - proba, 4)

    return {
        "label": label,
        "confidence": confidence,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        "model_available": True,
    }
