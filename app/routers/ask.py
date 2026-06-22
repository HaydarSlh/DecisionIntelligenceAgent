# ============================================================
# Router: /ask — Plain LLM and RAG-grounded answers
# ============================================================
# POST /ask     -> LLM answers from general knowledge only
# POST /ask/rag -> LLM answers grounded in retrieved tickets
# ============================================================

import time
import logging

from fastapi import APIRouter, HTTPException

from app.config import RAG_TOP_K
from app.models import TicketRequest, PlainAnswerResponse, RAGAnswerResponse, RetrievedTicket
from app.llm import call_llm_with_stats, get_model_name
from app.prompts.plain_answer import PLAIN_SYSTEM_PROMPT
from app.prompts.grounded_answer import RAG_SYSTEM_PROMPT
from app.rag.embedder import embed_text
from app.rag.store import search, count
from app.query_logger import log_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ask", tags=["Q&A"])


@router.post("", response_model=PlainAnswerResponse)
def ask_plain(request: TicketRequest):
    """Answer a support question using only the LLM's general knowledge."""
    try:
        stats = call_llm_with_stats(
            user_prompt=request.text,
            system_prompt=PLAIN_SYSTEM_PROMPT,
        )
    except Exception as exc:
        logger.error("LLM plain call failed: %s", exc)
        raise HTTPException(status_code=503, detail=f"LLM unavailable: {exc}") from exc
    log_query("ask_plain", {
        "query": request.text,
        "answer": stats["text"],
        "latency_ms": stats["latency_ms"],
        "input_tokens": stats["input_tokens"],
        "output_tokens": stats["output_tokens"],
        "cost_usd": stats["cost_usd"],
    })
    return PlainAnswerResponse(
        answer=stats["text"],
        model=get_model_name(),
        latency_ms=stats["latency_ms"],
    )


@router.post("/rag", response_model=RAGAnswerResponse)
def ask_rag(
    request: TicketRequest,
    top_k: int = RAG_TOP_K,
    brand: str | None = None,
):
    """Answer grounded in the top-k most similar conversation threads.

    top_k defaults to RAG_TOP_K (5 — one chunk per retrieved conversation).
    brand optionally restricts retrieval to threads for a given company handle.
    """
    t0 = time.perf_counter()

    retrieved: list[RetrievedTicket] = []
    if count() > 0:
        query_embedding = embed_text(request.text)
        raw_results = search(query_embedding, top_k=top_k, brand=brand)
        retrieved = [
            RetrievedTicket(
                text=r["text"],
                source=r.get("source") or "",
                distance=round(r["distance"], 4),
                priority=r.get("priority"),
                brand=r.get("brand"),
                thread_id=r.get("thread_id"),
            )
            for r in raw_results
        ]

    # Build context string from retrieved conversation threads
    if retrieved:
        context_parts = []
        for i, t in enumerate(retrieved, 1):
            brand_tag = f"[{t.brand}] " if t.brand else ""
            context_parts.append(
                f"Conversation {i} (similarity={1 - t.distance:.2f}) {brand_tag}\n{t.text}"
            )
        context = "\n\n---\n\n".join(context_parts)
    else:
        context = "No similar conversations found in the knowledge base."

    system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
    stats = call_llm_with_stats(
        user_prompt=request.text,
        system_prompt=system_prompt,
    )
    total_latency = round((time.perf_counter() - t0) * 1000, 2)

    log_query("ask_rag", {
        "query": request.text,
        "brand_filter": brand,
        "top_k": top_k,
        "retrieved_count": len(retrieved),
        "retrieved_distances": [r.distance for r in retrieved],
        "retrieved_brands": [r.brand for r in retrieved],
        "retrieved_thread_ids": [r.thread_id for r in retrieved],
        "answer": stats["text"],
        "latency_ms": total_latency,
        "input_tokens": stats["input_tokens"],
        "output_tokens": stats["output_tokens"],
        "cost_usd": stats["cost_usd"],
    })

    return RAGAnswerResponse(
        answer=stats["text"],
        model=get_model_name(),
        latency_ms=total_latency,
        retrieved_tickets=retrieved,
    )
