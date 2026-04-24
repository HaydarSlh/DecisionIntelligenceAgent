# ============================================================
# Vector Store — ChromaDB wrapper for storing and searching chunks
# ============================================================
# ChromaDB stores our chunks alongside their vector embeddings.
# When we search, it finds the chunks whose vectors are closest
# to the query vector — that means "most similar in meaning."
#
# This module is intentionally thin: just a few functions
# around ChromaDB's Python API. No abstraction layers.
# ============================================================

import chromadb
from app.config import CHROMA_PATH

COLLECTION_NAME = "acme_knowledge"


def get_client() -> chromadb.ClientAPI:
    """Create a persistent ChromaDB client."""
    return chromadb.PersistentClient(path=CHROMA_PATH)


def get_collection():
    """Get or create the knowledge base collection using cosine distance."""
    client = get_client()
    # Cosine is the standard metric for text embeddings — invariant to
    # vector magnitude, unlike the default L2 (Euclidean) distance.
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# Purpose: Store chunks with their embeddings. Upsert so re-ingesting
# updates rather than duplicates.
CHROMA_BATCH_SIZE = 500

def add_chunks(chunks: list[dict], embeddings: list[list[float]]) -> int:
    """Store chunks with their embeddings in ChromaDB.

    Optional metadata keys on a chunk (brand, thread_id, n_messages) are
    persisted as-is so we can filter on them at query time.
    Upserts in batches of CHROMA_BATCH_SIZE to stay under ChromaDB's hard limit.
    """
    collection = get_collection()

    ids = [f"{c['source']}_{c['chunk_index']}" for c in chunks]
    documents = [c["text"] for c in chunks]

    metadatas = []
    for c in chunks:
        md = {"source": c["source"], "chunk_index": c["chunk_index"]}
        for key in ("brand", "thread_id", "n_messages"):
            if key in c and c[key] is not None:
                md[key] = c[key]
        metadatas.append(md)

    for i in range(0, len(chunks), CHROMA_BATCH_SIZE):
        collection.upsert(
            ids=ids[i:i + CHROMA_BATCH_SIZE],
            documents=documents[i:i + CHROMA_BATCH_SIZE],
            embeddings=embeddings[i:i + CHROMA_BATCH_SIZE],
            metadatas=metadatas[i:i + CHROMA_BATCH_SIZE],
        )

    return len(chunks)


# Purpose: Search for the most similar chunks to a query vector.
def search(
    query_embedding: list[float],
    top_k: int = 3,
    brand: str | None = None,
) -> list[dict]:
    """
    Search for the most similar chunks to a query vector.
    Lower distance = more similar = more relevant.

    If `brand` is set, restrict to chunks whose metadata brand matches
    (case-insensitive, but Chroma compares exact strings — we canonicalize
    the stored brand to the handle we saved during ingestion).
    """
    collection = get_collection()

    n_stored = collection.count()
    if n_stored == 0:
        return []
    actual_k = min(top_k, n_stored)

    query_kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": actual_k,
    }
    if brand:
        query_kwargs["where"] = {"brand": brand}

    results = collection.query(**query_kwargs)

    items = []
    for i in range(len(results["ids"][0])):
        md = results["metadatas"][0][i] or {}
        items.append({
            "text": results["documents"][0][i],
            "source": md.get("source"),
            "chunk_index": md.get("chunk_index"),
            "brand": md.get("brand"),
            "thread_id": md.get("thread_id"),
            "distance": results["distances"][0][i],
        })

    return items


def count() -> int:
    """Count how many chunks are stored."""
    return get_collection().count()


# Purpose: List every unique source filename currently in the store.
def get_all_sources() -> list[str]:
    """Return all unique source filenames present in the vector store."""
    collection = get_collection()
    if collection.count() == 0:
        return []
    data = collection.get(include=["metadatas"])
    sources = {m["source"] for m in data["metadatas"] if m and "source" in m}
    return sorted(sources)


# Purpose: Retrieve stored chunks for inspection.
def get_all_chunks(
    source: str | None = None,
    limit: int = 50,
    include_embeddings: bool = False,
) -> list[dict]:
    """Retrieve stored chunks for inspection."""
    collection = get_collection()

    if collection.count() == 0:
        return []

    includes = ["documents", "metadatas"]
    if include_embeddings:
        includes.append("embeddings")

    kwargs = {"limit": limit, "include": includes}
    if source:
        kwargs["where"] = {"source": source}

    data = collection.get(**kwargs)

    items = []
    for i in range(len(data["ids"])):
        item = {
            "id": data["ids"][i],
            "text": data["documents"][i],
            "source": data["metadatas"][i]["source"],
            "chunk_index": data["metadatas"][i]["chunk_index"],
        }
        if include_embeddings and data.get("embeddings") is not None:
            emb = list(data["embeddings"][i])
            item["embedding_preview"] = emb[:5]
            item["embedding_dimensions"] = len(emb)
        items.append(item)

    return items


def clear():
    """Delete all chunks. Useful for re-ingesting from scratch."""
    client = get_client()
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
