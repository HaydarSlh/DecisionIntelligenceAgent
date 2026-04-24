# ============================================================
# Router: /priority — ML and LLM urgency classifiers
# ============================================================
# POST /priority/ml    -> trained LightGBM classifier
# POST /priority/llm   -> Gemini 2.5 Flash zero-shot
# POST /priority/compare -> both predictions side by side
# ============================================================

import json
import logging
import re

import traceback

from fastapi import APIRouter, HTTPException

from app.models import TicketRequest, PriorityMLResponse, PriorityLLMResponse
from app.ml_model import predict_priority as ml_predict
from app.llm import call_llm_with_stats, get_model_name
from app.prompts.priority_llm import PRIORITY_SYSTEM_PROMPT
from app.query_logger import log_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/priority", tags=["Priority Prediction"])


@router.post("/ml", response_model=PriorityMLResponse)
def predict_ml(request: TicketRequest):
    """Predict ticket urgency using the trained ML pipeline (LightGBM)."""
    result = ml_predict(request.text)
    log_query("priority_ml", {
        "query": request.text,
        **result,
    })
    return PriorityMLResponse(**result)


@router.post("/llm", response_model=PriorityLLMResponse)
def predict_llm(request: TicketRequest):
    """Predict ticket urgency using Gemini 2.5 Flash zero-shot classification."""
    try:
        stats = call_llm_with_stats(
            user_prompt=request.text,
            system_prompt=PRIORITY_SYSTEM_PROMPT,
        )
    except Exception as exc:
        logger.error("LLM priority call failed: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}") from exc

    parsed = _parse_priority_response(stats["text"])

    log_query("priority_llm", {
        "query": request.text,
        "label": parsed["label"],
        "confidence": parsed["confidence"],
        "explanation": parsed["explanation"],
        "latency_ms": stats["latency_ms"],
        "input_tokens": stats["input_tokens"],
        "output_tokens": stats["output_tokens"],
        "cost_usd": stats["cost_usd"],
    })

    return PriorityLLMResponse(
        label=parsed["label"],
        confidence=parsed["confidence"],
        explanation=parsed["explanation"],
        model=get_model_name(),
        latency_ms=stats["latency_ms"],
        input_tokens=stats["input_tokens"],
        output_tokens=stats["output_tokens"],
        cost_usd=stats["cost_usd"],
    )


def _parse_priority_response(text: str) -> dict:
    """Parse the LLM JSON response. Falls back gracefully on malformed output."""
    # Strip markdown code fences if present
    clean = re.sub(r"```(?:json)?|```", "", text).strip()

    try:
        data = json.loads(clean)
        label = str(data.get("label", "normal")).lower()
        if label not in ("urgent", "normal"):
            label = "normal"
        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
        explanation = str(data.get("explanation", ""))
        return {"label": label, "confidence": round(confidence, 4), "explanation": explanation}
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse LLM priority JSON: %s", text[:200])
        # Best-effort fallback: look for the word urgent/normal in the raw text
        lower = text.lower()
        label = "urgent" if "urgent" in lower else "normal"
        return {
            "label": label,
            "confidence": 0.5,
            "explanation": "Could not parse structured response from LLM.",
        }
