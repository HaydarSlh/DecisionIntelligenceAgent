# ============================================================
# Router: /embed — Explore how embeddings work
# ============================================================
# Teaching tool. Embed any texts and see how "close" or "far"
# they are in vector space. Low distance = similar meaning.
#
# TRY THESE EXPERIMENTS:
#
#   1. Synonyms:
#      ["vacation days", "annual leave", "time off"]
#      -> All three should be close
#
#   2. Same topic vs different topic:
#      ["vacation days", "annual leave", "Python programming"]
#      -> First pair close, other pairs far
#
#   3. Question vs answer match:
#      ["How many vacation days?", "Employees receive 20 days of annual leave"]
#      -> Should be fairly close (good for RAG!)
#
#   4. Different languages, same meaning:
#      ["vacation", "vacaciones", "urlaub"]
#      -> Often close, depending on the embedding model
# ============================================================

import math
from fastapi import APIRouter
from app.models import EmbedRequest, EmbedResponse, PairwiseDistance
from app.rag.embedder import embed_texts

router = APIRouter(prefix="/embed", tags=["Embedding Explorer"])


# Purpose: Convert a raw L2 distance into a human-readable similarity bucket.
# Assumes unit-normalized embeddings (OpenAI/Gemini), so distance ∈ [0, 2].
def _similarity_label(distance: float) -> str:
    if distance < 0.4:
        return "very similar"
    if distance < 0.7:
        return "similar"
    if distance < 1.0:
        return "somewhat similar"
    if distance < 1.3:
        return "not similar"
    return "very different"


@router.post("", response_model=EmbedResponse)
def explore_embeddings(request: EmbedRequest):
    """
    Embed a list of texts and compute pairwise distances.

    Send 2+ texts to see how similar they are in vector space.
    Each pair gets both a numeric distance and a similarity label.
    """
    texts = request.texts

    embeddings = embed_texts(texts)
    dimensions = len(embeddings[0]) if embeddings else 0

    distances = {}
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            # L2 distance: sqrt(sum((a_k - b_k)^2))
            dist = math.sqrt(
                sum(
                    (embeddings[i][k] - embeddings[j][k]) ** 2
                    for k in range(dimensions)
                )
            )
            label = f"'{texts[i]}' <-> '{texts[j]}'"
            distances[label] = PairwiseDistance(
                distance=round(dist, 4),
                similarity=_similarity_label(dist),
            )

    return EmbedResponse(distances=distances, dimensions=dimensions)
