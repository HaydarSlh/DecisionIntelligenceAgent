# ============================================================
# LLM caller — thin wrapper around the LLM client
# ============================================================
# Supports Gemini, OpenAI, and Azure OpenAI via LLM_PROVIDER.
# call_llm()           -> str  (plain response text)
# call_llm_with_stats() -> dict (text + tokens + latency + cost)
# ============================================================

import time
import logging
from functools import lru_cache

# Gemini 2.5 Flash pricing (USD per 1M tokens, prompts ≤ 200K tokens)
_GEMINI_INPUT_PRICE_PER_M = 0.075
_GEMINI_OUTPUT_PRICE_PER_M = 0.30

from app.config import (
    LLM_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT,
)

logger = logging.getLogger(__name__)

LLM_MAX_RETRIES = 3
LLM_RETRY_DELAY = 1.0


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


# Purpose: Returns the model name string for the active LLM provider.
def get_model_name() -> str:
    """Return the model name for the active provider."""
    if LLM_PROVIDER == "gemini":
        return GEMINI_MODEL
    if LLM_PROVIDER == "openai":
        return OPENAI_MODEL
    return AZURE_OPENAI_DEPLOYMENT


# Purpose: Sends a prompt to the configured LLM with retry/backoff.
def call_llm(user_prompt: str, system_prompt: str = "") -> str:
    """
    Send a prompt to the LLM and return the response text.

    Uses Gemini, OpenAI, or Azure OpenAI based on LLM_PROVIDER.
    Retries up to LLM_MAX_RETRIES times with exponential backoff.
    """
    for attempt in range(LLM_MAX_RETRIES):
        try:
            if LLM_PROVIDER == "gemini":
                return _call_gemini(user_prompt, system_prompt)
            if LLM_PROVIDER == "openai":
                return _call_openai(user_prompt, system_prompt)
            return _call_azure(user_prompt, system_prompt)
        except Exception as e:
            logger.warning(
                "LLM call failed (attempt %d/%d): %s",
                attempt + 1,
                LLM_MAX_RETRIES,
                e,
            )
            if attempt == LLM_MAX_RETRIES - 1:
                raise
            time.sleep(LLM_RETRY_DELAY * (2 ** attempt))


def call_llm_with_stats(user_prompt: str, system_prompt: str = "") -> dict:
    """Call LLM and return text plus usage statistics.

    Returns dict with keys:
        text         - the response string
        input_tokens - prompt token count (Gemini only; 0 for other providers)
        output_tokens - completion token count (Gemini only; 0 for other providers)
        latency_ms   - wall-clock milliseconds for the call
        cost_usd     - estimated cost in USD (Gemini 2.5 Flash pricing)
    """
    t0 = time.perf_counter()
    for attempt in range(LLM_MAX_RETRIES):
        try:
            if LLM_PROVIDER == "gemini":
                result = _call_gemini_with_stats(user_prompt, system_prompt)
            else:
                text = call_llm(user_prompt, system_prompt)
                result = {"text": text, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
            result["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            return result
        except Exception as e:
            logger.warning(
                "LLM call failed (attempt %d/%d): %s", attempt + 1, LLM_MAX_RETRIES, e
            )
            if attempt == LLM_MAX_RETRIES - 1:
                raise
            time.sleep(LLM_RETRY_DELAY * (2 ** attempt))


def _call_gemini_with_stats(user_prompt: str, system_prompt: str) -> dict:
    """Call Gemini and return text + token usage."""
    from google.genai import types

    client = _get_gemini_client()
    config = types.GenerateContentConfig(temperature=0.3)
    if system_prompt:
        config.system_instruction = system_prompt

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=config,
    )

    usage = response.usage_metadata
    input_tokens = getattr(usage, "prompt_token_count", 0) or 0
    output_tokens = getattr(usage, "candidates_token_count", 0) or 0
    cost_usd = (
        input_tokens * _GEMINI_INPUT_PRICE_PER_M +
        output_tokens * _GEMINI_OUTPUT_PRICE_PER_M
    ) / 1_000_000

    return {
        "text": response.text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost_usd, 8),
    }


def _call_gemini(user_prompt: str, system_prompt: str) -> str:
    """Call Google Gemini API with system instruction support."""
    return _call_gemini_with_stats(user_prompt, system_prompt)["text"]


def _call_openai(user_prompt: str, system_prompt: str) -> str:
    """Call OpenAI API."""
    client = _get_openai_client()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.3,
    )

    return response.choices[0].message.content


def _call_azure(user_prompt: str, system_prompt: str) -> str:
    """Call Azure OpenAI API."""
    client = _get_azure_client()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=messages,
        temperature=0.3,
    )

    return response.choices[0].message.content
