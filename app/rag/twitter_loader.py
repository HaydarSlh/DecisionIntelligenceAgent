# ============================================================
# Twitter Loader — reads twcs_raw.parquet into conversation threads
# ============================================================
# METHODOLOGY
#   - A "thread" is one whole support conversation.
#   - It starts at a root tweet (in_response_to_tweet_id is null)
#     and ends at leaf tweets (response_tweet_id is null).
#   - We walk forward from each root through `response_tweet_id`
#     (which may list multiple children, comma-separated) until
#     every reachable descendant is collected, then emit one
#     chunk per connected conversation.
#   - Each thread carries a `brand` tag (the non-inbound author
#     most present in the conversation) so retrieval can be
#     filtered by brand.
# ============================================================

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def _split_children(cell) -> list[int]:
    """`response_tweet_id` stores one id or a comma-separated list as a string."""
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return []
    text = str(cell).strip()
    if not text or text.lower() == "nan":
        return []
    out = []
    for tok in text.split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            out.append(int(float(tok)))
        except ValueError:
            continue
    return out


def _format_thread_text(rows: list[dict]) -> str:
    """Render a thread as alternating CUSTOMER / BRAND turns, in chronological order."""
    rows = sorted(rows, key=lambda r: (r.get("created_at") or "", r["tweet_id"]))
    lines = []
    for r in rows:
        role = "CUSTOMER" if r["inbound"] else "BRAND"
        author = r["author_id"]
        msg = (r["text"] or "").replace("\n", " ").strip()
        lines.append(f"{role} ({author}): {msg}")
    return "\n".join(lines)


def _pick_brand(rows: list[dict]) -> str:
    """The brand of a thread = the non-inbound author with the most messages."""
    counts: dict[str, int] = {}
    for r in rows:
        if not r["inbound"]:
            counts[r["author_id"]] = counts.get(r["author_id"], 0) + 1
    if not counts:
        return "unknown"
    return max(counts.items(), key=lambda kv: kv[1])[0]


def load_threads(
    parquet_path: str,
    limit: int | None = None,
    brand: str | None = None,
    min_messages: int = 2,
) -> list[dict]:
    """
    Build conversation threads from the twcs parquet.

    Args:
        parquet_path: path to twcs_raw.parquet.
        limit: optional cap on number of threads returned (after filtering).
        brand: optional brand filter — only keep threads whose dominant
               non-inbound author matches this handle (case-insensitive).
        min_messages: drop threads shorter than this (default 2 so we always
                      have at least a customer + brand turn).

    Returns:
        list of dicts with keys:
            thread_id      -> root tweet_id (str)
            brand          -> dominant non-inbound author handle
            n_messages     -> number of tweets in the thread
            text           -> rendered conversation
    """
    path = Path(parquet_path)
    if not path.exists():
        raise FileNotFoundError(f"Parquet not found: {path}")

    logger.info("Loading parquet %s", path)
    df = pd.read_parquet(path)
    logger.info("Loaded %d tweets", len(df))

    # Index rows by tweet_id for O(1) lookup
    by_id: dict[int, dict] = {}
    for rec in df.to_dict(orient="records"):
        by_id[int(rec["tweet_id"])] = rec

    # Roots = tweets with no parent
    roots = [
        tid for tid, r in by_id.items()
        if pd.isna(r.get("in_response_to_tweet_id"))
    ]
    logger.info("Found %d thread roots", len(roots))

    threads: list[dict] = []
    visited: set[int] = set()

    for root_id in roots:
        if root_id in visited:
            continue

        # BFS over response_tweet_id to collect all descendants of this root
        collected: list[dict] = []
        stack = [root_id]
        while stack:
            tid = stack.pop()
            if tid in visited or tid not in by_id:
                continue
            visited.add(tid)
            r = by_id[tid]
            collected.append(r)
            for child in _split_children(r.get("response_tweet_id")):
                if child not in visited:
                    stack.append(child)

        if len(collected) < min_messages:
            continue

        thread_brand = _pick_brand(collected)
        if brand and thread_brand.lower() != brand.lower():
            continue

        threads.append({
            "thread_id": str(root_id),
            "brand": thread_brand,
            "n_messages": len(collected),
            "text": _format_thread_text(collected),
        })

        if limit is not None and len(threads) >= limit:
            break

    logger.info("Built %d threads (limit=%s, brand=%s)", len(threads), limit, brand)
    return threads
