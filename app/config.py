# ============================================================
# Configuration — loaded from environment variables
# ============================================================
# All settings are read from environment variables with safe
# defaults. Copy .env.example to .env and fill in your API keys.
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM provider: "gemini", "openai", or "azure" ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# --- Gemini settings (used when LLM_PROVIDER=gemini) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

# --- OpenAI settings (used when LLM_PROVIDER=openai) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# --- Azure OpenAI settings (used when LLM_PROVIDER=azure) ---
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "")

# --- Data settings ---
KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", "data/knowledge")

# --- Chunking settings ---
DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "500"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "50"))

# --- Supported file types for ingestion ---
SUPPORTED_EXTENSIONS = [".md", ".txt", ".csv", ".pdf", ".json"]

# --- Vector store settings ---
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_data")

# --- Logs ---
LOGS_DIR = os.getenv("LOGS_DIR", "./logs")

# --- ML model paths ---
MODEL_PATH = os.getenv("MODEL_PATH", "./models/priority_model.joblib")
THRESHOLD_PATH = os.getenv("THRESHOLD_PATH", "./models/decision_threshold.json")

# --- Twitter thread-RAG settings ---
# Path to the cleaned parquet built from the twcs Kaggle dump.
TWCS_PARQUET_PATH = os.getenv("TWCS_PARQUET_PATH", "./dataset/processed/twcs_raw.parquet")
# Max characters per chunk before halving; sized for gemini-embedding-001.
THREAD_MAX_CHARS = int(os.getenv("THREAD_MAX_CHARS", "4000"))
# Top-k conversations retrieved per user query.
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
# Optional safety cap on how many threads to ingest in one run.
THREAD_INGEST_LIMIT = int(os.getenv("THREAD_INGEST_LIMIT", "0")) or None
# Threads shorter than this are skipped during ingestion.
THREAD_MIN_MESSAGES = int(os.getenv("THREAD_MIN_MESSAGES", "2"))
