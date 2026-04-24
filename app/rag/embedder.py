# ============================================================
# Embedder — turns text into vector embeddings
# ============================================================
# An embedding is a list of numbers (a vector) that captures
# the MEANING of a piece of text. Similar meanings produce
# similar vectors. This is how we search by meaning instead
# of by keywords.
#
# Supports Gemini, OpenAI, and Azure OpenAI embeddings.
# Includes retry logic for transient failures.
# ============================================================

import time
import logging
from functools import lru_cache

from app.config import (
    LLM_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_EMBEDDING_MODEL,
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
)

logger = logging.getLogger(__name__)

EMBED_MAX_RETRIES = 3
EMBED_RETRY_DELAY = 1.0
EMBED_BATCH_SIZE = 100


# Purpose: Cached client factories — reuse HTTP connections across calls.
@lru_cache(maxsize=1)
def _get_gemini_client():
    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


@lru_cache(maxsize=1)
def _get_openai_client():
    from openai import OpenAI
    return OpenAI(api_key=OPENAI_API_KEY)


@lru_cache(maxsize=1)
def _get_azure_client():
    from openai import AzureOpenAI
    return AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION,
    )


# Purpose: Embed a single text. Used for queries at search time.
def embed_text(text: str) -> list[float]:
    """Embed a single piece of text into a vector."""
    return embed_texts([text])[0]


# Purpose: Embed a batch of texts. Used for chunks at ingestion time.
def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts into vectors.

    Batches large inputs to respect API payload size limits and
    retries on transient failures with exponential backoff.
    """
    if len(texts) <= EMBED_BATCH_SIZE:
        return _embed_with_retry(texts)

    all_embeddings = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i:i + EMBED_BATCH_SIZE]
        logger.info("Embedding batch %d-%d of %d texts", i, i + len(batch), len(texts))
        all_embeddings.extend(_embed_with_retry(batch))
    return all_embeddings


def _embed_with_retry(texts: list[str]) -> list[list[float]]:
    """Embed texts with retry logic."""
    for attempt in range(EMBED_MAX_RETRIES):
        try:
            if LLM_PROVIDER == "gemini":
                return _embed_gemini(texts)
            if LLM_PROVIDER == "openai":
                return _embed_openai(texts)
            return _embed_azure(texts)
        except Exception as e:
            logger.warning(
                "Embedding call failed (attempt %d/%d): %s",
                attempt + 1,
                EMBED_MAX_RETRIES,
                e,
            )
            if attempt == EMBED_MAX_RETRIES - 1:
                raise
            time.sleep(EMBED_RETRY_DELAY * (2 ** attempt))


def _embed_gemini(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using Google Gemini."""
    client = _get_gemini_client()

    result = client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=texts,
    )

    return [embedding.values for embedding in result.embeddings]


def _embed_openai(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using OpenAI."""
    client = _get_openai_client()

    response = client.embeddings.create(
        model=OPENAI_EMBEDDING_MODEL,
        input=texts,
    )

    return [item.embedding for item in response.data]


def _embed_azure(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using Azure OpenAI."""
    client = _get_azure_client()

    response = client.embeddings.create(
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=texts,
    )

    return [item.embedding for item in response.data]
