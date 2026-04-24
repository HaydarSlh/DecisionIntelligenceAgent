# ============================================================
# Thread Chunker — one chunk per conversation, halved if too long
# ============================================================
# WHY
#   Gemini's embedding model has an input-token limit. Most twcs
#   conversations are short, but a minority can blow past the
#   limit. When a thread is too long, we split it in half at a
#   message boundary and recurse — each half keeps the same
#   thread_id and brand for metadata.
# ============================================================


# ~4000 chars ≈ ~1000 tokens — well under gemini-embedding-001's limit,
# with headroom for retrieval-time concatenation into the LLM prompt.
DEFAULT_MAX_CHARS = 4000


def chunk_threads(
    threads: list[dict],
    max_chars: int = DEFAULT_MAX_CHARS,
) -> list[dict]:
    """
    Turn a list of thread dicts into chunk dicts ready for the vector store.

    Args:
        threads: output of load_threads() — each has text, brand, thread_id.
        max_chars: any thread whose text exceeds this is split into halves
                   (recursively) at a message boundary.

    Returns:
        list of dicts with keys: text, source, chunk_index, brand, thread_id.
        `source` is the thread_id so store.add_chunks can build unique ids.
    """
    chunks: list[dict] = []
    for t in threads:
        pieces = _halve_if_needed(t["text"], max_chars)
        for i, piece in enumerate(pieces):
            chunks.append({
                "text": piece,
                "source": f"thread_{t['thread_id']}",
                "chunk_index": i,
                "brand": t["brand"],
                "thread_id": t["thread_id"],
                "n_messages": t["n_messages"],
            })
    return chunks


def _halve_if_needed(text: str, max_chars: int) -> list[str]:
    """If `text` fits, return [text]. Otherwise split at the nearest message
    boundary to the midpoint and recurse on each half."""
    if len(text) <= max_chars:
        return [text]

    lines = text.split("\n")
    if len(lines) <= 1:
        # Pathological single-line thread — fall back to a hard split.
        mid = len(text) // 2
        return _halve_if_needed(text[:mid], max_chars) + _halve_if_needed(text[mid:], max_chars)

    # Split as close to the middle line as possible so both halves have context.
    mid_line = len(lines) // 2
    first = "\n".join(lines[:mid_line]).strip()
    second = "\n".join(lines[mid_line:]).strip()

    if not first or not second:
        # Degenerate — bail out with a single chunk rather than loop.
        return [text]

    return _halve_if_needed(first, max_chars) + _halve_if_needed(second, max_chars)
