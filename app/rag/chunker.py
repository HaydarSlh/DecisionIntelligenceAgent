# ============================================================
# Chunker — splits a document into overlapping text chunks
# ============================================================
# WHY CHUNKING?
#   - LLMs have token limits — we can't paste entire documents.
#   - Even if we could, most of the document is irrelevant to
#     any single question. Chunks let us retrieve ONLY the
#     relevant pieces.
#
# WHY OVERLAP?
#   - A sentence might get split across two chunks.
#   - Overlap preserves context at chunk boundaries.
#
# TRADEOFFS:
#   - Small chunks (200 chars): precise retrieval, less context
#   - Large chunks (1000+): more context, less precise retrieval
#   - 400-600 is a reasonable starting point
# ============================================================

import re


def chunk_document(
    text: str,
    source: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict]:
    """
    Split a document into overlapping text chunks.

    Args:
        text: The full document text to split.
        source: Filename or identifier for this document.
        chunk_size: Maximum number of characters per chunk.
        overlap: Number of characters to overlap between chunks.

    Returns:
        A list of dicts, each with: text, source, chunk_index.
    """
    text = text.strip()

    if len(text) <= chunk_size:
        return [{"text": text, "source": source, "chunk_index": 0}]

    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Sentence-aware splitting: scan backward for a sentence boundary
        # so we don't cut mid-sentence. Produces better embeddings.
        if end < len(text):
            for boundary in (". ", ".\n", "? ", "!\n", "?\n", "!\n", "\n\n"):
                last_break = text.rfind(boundary, start, end)
                if last_break > start:
                    end = last_break + len(boundary)
                    break

        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "source": source,
                "chunk_index": chunk_index,
            })
            chunk_index += 1

        # Ensure start always moves forward to prevent infinite loops.
        if end >= len(text):
            start = end
        else:
            start = max(end - overlap, start + 1)

    return chunks


# ============================================================
# Section-based chunker — splits on paragraph or heading breaks
# ============================================================
# Alternative strategy: split on document structure (markdown
# headings or blank lines) instead of fixed character counts.
# Pros: chunks follow natural structure, no mid-sentence cuts.
# Cons: unpredictable chunk sizes; no overlap.
# ============================================================


def chunk_by_sections(text: str, source: str) -> list[dict]:
    """
    Split a document into chunks based on markdown headings or
    blank-line-separated paragraphs.
    """
    text = text.strip()

    # Try splitting on markdown headings first (## or #)
    sections = re.split(r"\n(?=#{1,3}\s)", text)

    # Fall back to splitting on double newlines
    if len(sections) <= 1:
        sections = re.split(r"\n\n+", text)

    chunks = []
    for i, section in enumerate(sections):
        section = section.strip()
        if section:
            chunks.append({
                "text": section,
                "source": source,
                "chunk_index": i,
            })

    return chunks
