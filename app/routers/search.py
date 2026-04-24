# ============================================================
# Router: /search — Test retrieval in isolation
# ============================================================
# This endpoint lets you search the vector store WITHOUT
# calling the LLM. It's a debugging and teaching tool.
#
# Pay attention to the DISTANCE scores:
#   Low distance (< 0.5)  = strongly relevant
#   High distance (> 1.0) = probably irrelevant
# ============================================================

from fastapi import APIRouter, Query
from app.models import SearchResponse, SearchResult
from app.rag.embedder import embed_text
from app.rag.store import search, count

router = APIRouter(prefix="/search", tags=["Search"])


# Purpose: Embed a query and return the most similar stored chunks.
@router.get("", response_model=SearchResponse)
def search_chunks(
    q: str = Query(description="The search query text."),
    top_k: int = Query(default=3, description="Number of results to return."),
):
    """Retrieval without generation — just finding relevant chunks."""
    stored = count()
    if stored == 0:
        return SearchResponse(query=q, results=[], total_results=0)

    query_embedding = embed_text(q)
    raw_results = search(query_embedding, top_k=top_k)

    results = [
        SearchResult(
            text=r["text"],
            source=r["source"],
            chunk_index=r["chunk_index"],
            distance=r["distance"],
        )
        for r in raw_results
    ]

    return SearchResponse(query=q, results=results, total_results=len(results))
