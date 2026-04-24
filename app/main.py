# ============================================================
# Main FastAPI app — Acme Corp Knowledge Assistant (API only)
# ============================================================
# The React frontend is served by a separate nginx container.
# nginx proxies API calls to this service in docker-compose.
# ============================================================

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-18s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("chromadb.telemetry").setLevel(logging.WARNING)
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai.models").setLevel(logging.WARNING)

from app.routers.ask import router as ask_router
from app.routers.ingest import router as ingest_router
from app.routers.ingest_threads import router as ingest_threads_router
from app.routers.search import router as search_router
from app.routers.inspect import router as inspect_router
from app.routers.embed import router as embed_router
from app.routers.priority import router as priority_router

app = FastAPI(
    title="Acme Corp Knowledge Assistant",
    description="RAG playground: ingest, embed, search, and ask against your own documents.",
    version="1.0.0",
)

# CORS — the React dev server (Vite on :5173) and production nginx
# proxy both need to hit this API from the browser.
_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:8080,http://127.0.0.1:5173,http://127.0.0.1:8080",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(ask_router)
app.include_router(ingest_router)
app.include_router(ingest_threads_router)
app.include_router(search_router)
app.include_router(inspect_router)
app.include_router(embed_router)
app.include_router(priority_router)


@app.get("/health", tags=["System"])
def health_check():
    """Simple health check — confirms the app is running."""
    return {"status": "ok"}
