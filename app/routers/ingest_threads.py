# ============================================================
# Router: /ingest/threads — Twitter conversation-thread RAG ingest
# ============================================================
# Flow:
#   1. Read the twcs parquet
#   2. Build threads (root = in_response_to_tweet_id null;
#      leaves = response_tweet_id null) as one chunk each
#   3. Halve any chunk that exceeds THREAD_MAX_CHARS
#   4. Embed with Gemini (gemini-embedding-001)
#   5. Upsert into Chroma with brand + thread_id metadata
# ============================================================

import logging

from fastapi import APIRouter, HTTPException, Query

from app.config import (
    TWCS_PARQUET_PATH,
    THREAD_MAX_CHARS,
    THREAD_INGEST_LIMIT,
    THREAD_MIN_MESSAGES,
)
from app.rag.twitter_loader import load_threads
from app.rag.thread_chunker import chunk_threads
from app.rag.embedder import embed_texts
from app.rag.store import add_chunks, clear

logger = logging.getLogger("rag.ingest_threads")
router = APIRouter(prefix="/ingest/threads", tags=["Ingestion"])


@router.post("")
def ingest_threads(
    limit: int | None = Query(
        default=THREAD_INGEST_LIMIT,
        description="Max threads to ingest (None = all).",
    ),
    brand: str | None = Query(
        default=None,
        description="Optional brand handle filter, e.g. 'AmazonHelp'.",
    ),
    max_chars: int = Query(
        default=THREAD_MAX_CHARS,
        description="Threads longer than this are split in half recursively.",
    ),
    min_messages: int = Query(
        default=THREAD_MIN_MESSAGES,
        description="Drop threads shorter than this many messages.",
    ),
    fresh: bool = Query(
        default=False,
        description="Clear the store before ingesting.",
    ),
):
    """Build and embed conversation threads from the twcs parquet."""
    logger.info(
        "Thread ingest | parquet=%s limit=%s brand=%s max_chars=%d min_messages=%d fresh=%s",
        TWCS_PARQUET_PATH, limit, brand, max_chars, min_messages, fresh,
    )

    if fresh:
        clear()
        logger.info("Store cleared")

    # --- Step 1: load threads ---
    try:
        threads = load_threads(
            parquet_path=TWCS_PARQUET_PATH,
            limit=limit,
            brand=brand,
            min_messages=min_messages,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Parquet file not found: {exc}") from exc
    except Exception as exc:
        logger.exception("Failed to load threads")
        raise HTTPException(status_code=500, detail=f"Error loading parquet: {type(exc).__name__}: {exc}") from exc

    if not threads:
        return {"threads_built": 0, "chunks_stored": 0, "brand_filter": brand}

    # --- Step 2: chunk ---
    try:
        chunks = chunk_threads(threads, max_chars=max_chars)
        logger.info("Thread chunking complete | %d threads -> %d chunks", len(threads), len(chunks))
    except Exception as exc:
        logger.exception("Failed to chunk threads")
        raise HTTPException(status_code=500, detail=f"Error chunking threads: {type(exc).__name__}: {exc}") from exc

    # --- Steps 3+4: embed and store in batches of 500 ---
    # Avoids holding all embeddings in memory and keeps each ChromaDB
    # upsert well under its 5461-item hard limit.
    BATCH = 500
    stored = 0
    try:
        for i in range(0, len(chunks), BATCH):
            batch = chunks[i:i + BATCH]
            try:
                embeddings = embed_texts([c["text"] for c in batch])
            except Exception as exc:
                logger.exception("Failed to embed batch %d-%d", i, i + len(batch))
                raise HTTPException(
                    status_code=500,
                    detail=f"Embedding API error on batch {i}-{i+len(batch)}: {type(exc).__name__}: {exc}",
                ) from exc
            try:
                stored += add_chunks(batch, embeddings)
            except Exception as exc:
                logger.exception("Failed to store batch %d-%d in ChromaDB", i, i + len(batch))
                raise HTTPException(
                    status_code=500,
                    detail=f"ChromaDB error on batch {i}-{i+len(batch)}: {type(exc).__name__}: {exc}",
                ) from exc
            logger.info("Stored %d/%d chunks", stored, len(chunks))
    except HTTPException:
        raise

    return {
        "threads_built": len(threads),
        "chunks_stored": stored,
        "brand_filter": brand,
        "max_chars": max_chars,
        "split_chunks": stored - len(threads),
    }
