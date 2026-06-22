# ============================================================
# Backend — FastAPI service
# ============================================================
# This image contains only the FastAPI app (app/).
# Heavy data (dataset, chroma_data, logs, models) are
# mounted at runtime via Docker Compose volumes so the image
# stays small and data survives container rebuilds.
# ============================================================

# python:3.12-slim is Debian-based without the full stdlib extras.
# We use it (not alpine) because chromadb's hnswlib C++ extension
# compiles against glibc — musl (alpine) would require extra patching.
FROM python:3.12-slim

WORKDIR /backend

# gcc / g++ are needed to compile hnswlib (chromadb's HNSW index).
# We remove the apt cache in the same RUN layer to keep layer size down.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the pinned requirements first.
# Docker caches this layer as long as the file doesn't change,
# so code edits won't trigger a full pip reinstall.
COPY requirements-backend.txt .
RUN uv install --no-cache-dir -r requirements-backend.txt

# Download the two NLTK corpora that vaderSentiment and the feature
# extractor need. Doing this at build time means the container starts
# instantly without a network call on first request.
RUN python -c "\
import nltk; \
nltk.download('punkt',     quiet=True); \
nltk.download('stopwords', quiet=True)"

# Copy only the application package — no dataset, no .env, no notebooks.
# Everything else is either mounted or injected via environment variables.
COPY app/ ./app/

EXPOSE 8000

# --host 0.0.0.0 is required inside Docker; without it uvicorn only
# listens on loopback (127.0.0.1) and the container is unreachable.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
