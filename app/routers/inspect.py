import json
from pathlib import Path
from fastapi import APIRouter, Query
from app.models import StoreInspectResponse, StoreSourcesResponse, StoredChunkInfo
from app.rag.store import get_all_chunks, get_all_sources
from app.config import LOGS_DIR

router = APIRouter(prefix="/store", tags=["Store Inspector"])

_METRICS_PATH = Path("models/metrics.json")


@router.get("/metrics", tags=["Store Inspector"])
def get_metrics():
    """Return ML model metrics from the notebook evaluation run.

    Returns models/metrics.json if it exists, otherwise a placeholder
    so the frontend always gets a valid response.
    """
    if _METRICS_PATH.exists():
        return json.loads(_METRICS_PATH.read_text(encoding="utf-8"))
    return {
        "note": "Run the urgency_model notebook to generate metrics.json",
        "accuracy": None,
        "f1": None,
        "precision": None,
        "recall": None,
    }


@router.get("/logs", tags=["Store Inspector"])
def get_query_logs(limit: int = Query(default=50, le=500)):
    """Return the most recent query log entries from queries.jsonl."""
    log_file = Path(LOGS_DIR) / "queries.jsonl"
    if not log_file.exists():
        return {"entries": [], "total": 0}
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    # Return most recent `limit` entries, newest first
    recent = lines[-limit:][::-1]
    entries = []
    for line in recent:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"entries": entries, "total": len(lines)}


@router.get("/sources", response_model=StoreSourcesResponse)
def list_sources():
    """List all unique source filenames present in the vector store."""
    return StoreSourcesResponse(sources=get_all_sources())


@router.get("/inspect", response_model=StoreInspectResponse)
def inspect_store(
    source: str | None = Query(default=None),
    show_embeddings: bool = Query(default=False),
    limit: int = Query(default=50, le=500),
):
    """Inspect the contents of the vector store."""
    raw = get_all_chunks(source=source, limit=limit, include_embeddings=show_embeddings)

    chunks = []
    for item in raw:
        chunk = StoredChunkInfo(
            id=item["id"],
            text=item["text"],
            source=item["source"],
            chunk_index=item["chunk_index"],
            embedding_preview=item.get("embedding_preview"),
            embedding_dimensions=item.get("embedding_dimensions"),
        )
        chunks.append(chunk)

    sources = sorted(set(c.source for c in chunks))

    return StoreInspectResponse(
        total_stored=len(chunks),
        sources=sources,
        chunks=chunks,
    )
