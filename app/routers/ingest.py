# ============================================================
# Router: /ingest — Load, chunk, embed, and store documents
# ============================================================
# The flow: Read files -> Chunk -> Embed -> Store in ChromaDB
# ============================================================

import logging
from pathlib import Path
from fastapi import APIRouter, Query
from app.config import (
    KNOWLEDGE_DIR,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    SUPPORTED_EXTENSIONS,
)
from app.models import IngestResponse, ChunkInfo
from app.rag.chunker import chunk_document, chunk_by_sections
from app.rag.loader import load_file
from app.rag.embedder import embed_texts
from app.rag.store import add_chunks, clear

logger = logging.getLogger("rag.ingest")
router = APIRouter(prefix="/ingest", tags=["Ingestion"])


# Purpose: Load, chunk, embed, and store all files in the knowledge base.
@router.post("", response_model=IngestResponse)
def ingest_documents(
    chunk_size: int = Query(
        default=DEFAULT_CHUNK_SIZE,
        description="Max characters per chunk (used with 'fixed' strategy).",
    ),
    overlap: int = Query(
        default=DEFAULT_CHUNK_OVERLAP,
        description="Characters of overlap between chunks (used with 'fixed' strategy).",
    ),
    chunk_strategy: str = Query(
        default="fixed",
        description="Chunking strategy: 'fixed' or 'sections'.",
    ),
    fresh: bool = Query(
        default=False,
        description="Set to true to clear the store before ingesting.",
    ),
):
    """Load all supported files, chunk them, embed them, and store in ChromaDB."""
    logger.info("Ingest started | strategy=%s chunk_size=%d overlap=%d fresh=%s",
                chunk_strategy, chunk_size, overlap, fresh)

    if fresh:
        clear()
        logger.info("Store cleared")

    knowledge_path = Path(KNOWLEDGE_DIR)
    logger.info("Knowledge dir: %s (exists=%s)", knowledge_path, knowledge_path.exists())

    if not knowledge_path.exists():
        logger.warning("Knowledge directory not found: %s", knowledge_path)
        return IngestResponse(
            files_processed=0, total_chunks=0, chunks_stored=0, chunks=[]
        )

    all_chunks = []
    files_processed = 0

    for filepath in sorted(knowledge_path.iterdir()):
        if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        text = load_file(str(filepath))
        filename = filepath.name

        if chunk_strategy == "sections":
            doc_chunks = chunk_by_sections(text=text, source=filename)
        else:
            doc_chunks = chunk_document(
                text=text,
                source=filename,
                chunk_size=chunk_size,
                overlap=overlap,
            )

        all_chunks.extend(doc_chunks)
        files_processed += 1
        logger.info("Loaded %s -> %d chunks", filename, len(doc_chunks))

    logger.info("Chunking complete | %d files -> %d total chunks", files_processed, len(all_chunks))

    logger.info("Starting embedding of %d chunks...", len(all_chunks))
    chunk_texts = [c["text"] for c in all_chunks]
    embeddings = embed_texts(chunk_texts)
    logger.info("Embedding complete | %d vectors", len(embeddings))

    logger.info("Storing in ChromaDB...")
    chunks_stored = add_chunks(all_chunks, embeddings)
    logger.info("Storage complete | %d chunks stored", chunks_stored)

    chunk_infos = [
        ChunkInfo(
            text=chunk["text"],
            source=chunk["source"],
            chunk_index=chunk["chunk_index"],
        )
        for chunk in all_chunks
    ]

    return IngestResponse(
        files_processed=files_processed,
        total_chunks=len(chunk_infos),
        chunks_stored=chunks_stored,
        chunks=chunk_infos,
    )
