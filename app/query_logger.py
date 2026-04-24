# ============================================================
# Query Logger — append-only JSONL log of every request
# ============================================================
# Tracks: query text, retrieved tickets, all system outputs,
# latency, cost, and errors — as required by the project brief.
# ============================================================

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.config import LOGS_DIR

logger = logging.getLogger(__name__)

_log_file = Path(LOGS_DIR) / "queries.jsonl"


def log_query(event_type: str, data: dict) -> None:
    """Append a structured record to the JSONL query log.

    Args:
        event_type: e.g. "ask_plain", "ask_rag", "priority_ml", "priority_llm", "compare"
        data: arbitrary dict — merged with timestamp and event_type
    """
    try:
        Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            **data,
        }
        with open(_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception as exc:
        logger.warning("Failed to write query log: %s", exc)
