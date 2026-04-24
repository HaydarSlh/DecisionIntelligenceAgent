# DecisionAgent

A production-grade AI decision support system that compares RAG, direct LLM, ML classifiers, and zero-shot LLM across two tasks: **Customer Support Q&A** and **Ticket Priority Prediction**.

Built with FastAPI, ChromaDB, LightGBM, Gemini, and React.

---

## What This App Does

DecisionAgent answers two questions side-by-side and lets you compare how each method performs:

1. **Customer Support Q&A**: When a customer submits a question, should you answer it with a RAG pipeline (grounded in real past conversations) or a direct LLM call (from general knowledge)?
2. **Ticket Priority Prediction**: When a support ticket arrives, should you classify its urgency with a trained ML model or a zero-shot LLM prompt?

For each task, the app shows the answer from both approaches simultaneously, with latency, cost, confidence gauges, bar charts, and a written recommendation on which to deploy in production.

---

## Architecture Overview

```
Customer query
      │
      ├─── /ask/rag ─────► embed query ──► ChromaDB search ──► Gemini LLM (grounded)
      │                                        (top-5 threads)
      │
      └─── /ask ──────────────────────────────────────────────► Gemini LLM (direct)

Support ticket
      │
      ├─── /priority/ml ──► feature extraction (20 features) ──► LightGBM classifier
      │
      └─── /priority/llm ─────────────────────────────────────► Gemini zero-shot JSON
```

**Backend:** FastAPI (Python 3.12)  
**Vector Store:** ChromaDB (persistent, cosine similarity)  
**Embeddings:** Gemini `gemini-embedding-001` (3072 dimensions)  
**LLM:** Gemini `gemini-2.5-flash` (configurable to OpenAI or Azure)  
**ML Model:** LightGBM binary classifier  
**Frontend:** React 18 + Vite + Recharts  
**Data:** [Twitter Customer Support dataset (twcs)](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter) — 2.8M tweets

---

## Project Structure

```
DecisionAgent/
├── app/
│   ├── main.py                  # FastAPI app, CORS, router registration
│   ├── config.py                # All env-variable settings
│   ├── llm.py                   # Gemini/OpenAI/Azure wrapper with retry + cost tracking
│   ├── ml_model.py              # LightGBM model loader and inference
│   ├── feature_extractor.py     # 20-feature text extractor (VADER, keywords, stats)
│   ├── query_logger.py          # Append-only JSONL query logger
│   ├── models.py                # Pydantic request/response schemas
│   ├── prompts/
│   │   ├── grounded_answer.py   # RAG system prompt — strict grounding, no hallucination
│   │   ├── plain_answer.py      # Direct LLM system prompt
│   │   └── priority_llm.py      # Zero-shot urgency classifier prompt (JSON output)
│   ├── rag/
│   │   ├── loader.py            # File reader (.md .txt .csv .pdf .json)
│   │   ├── chunker.py           # Fixed-size + section-based text chunking
│   │   ├── embedder.py          # Batch embedding with retry/backoff
│   │   ├── store.py             # ChromaDB wrapper (upsert, search, inspect)
│   │   ├── twitter_loader.py    # Parquet → conversation threads
│   │   └── thread_chunker.py    # Recursive thread splitting by message boundary
│   └── routers/
│       ├── ask.py               # POST /ask, POST /ask/rag
│       ├── priority.py          # POST /priority/ml, POST /priority/llm
│       ├── ingest.py            # POST /ingest (file-based)
│       ├── ingest_threads.py    # POST /ingest/threads (Twitter parquet)
│       ├── search.py            # GET /search
│       ├── embed.py             # POST /embed (pairwise similarity explorer)
│       └── inspect.py           # GET /store/* (inspect, sources, logs, metrics)
├── frontend/
│   ├── src/
│   │   ├── main.jsx             # React root; React Router (/ and /logs routes)
│   │   ├── App.jsx              # Mode state, orchestrates dashboards
│   │   ├── api.js               # HTTP client, parallel query runner
│   │   ├── App.css              # Full design system (dark theme)
│   │   ├── logs.css             # Logs page styles
│   │   ├── components/
│   │   │   ├── ModeNav.jsx          # Mode toggle (Customer Support / Priority)
│   │   │   ├── QueryForm.jsx        # Text input, brand filter, submit
│   │   │   ├── AnswerDashboard.jsx  # RAG vs Direct comparison view
│   │   │   ├── AnswerCard.jsx       # Single answer card (text, model, latency)
│   │   │   ├── PriorityDashboard.jsx # ML vs LLM comparison view
│   │   │   ├── PredictorCard.jsx    # Single predictor card (label, gauge, metrics)
│   │   │   └── ConfidenceGauge.jsx  # Animated SVG semicircle gauge
│   │   └── pages/
│   │       └── LogsPage.jsx         # /logs — query history with stats and filters
│   ├── vite.config.js           # Dev proxy to :8000, SPA history fallback
│   └── package.json
├── dataset/
│   └── processed/
│       └── twcs_raw.parquet     # Twitter customer support data (add manually)
├── models/
│   ├── priority_model.joblib    # Trained LightGBM pipeline
│   ├── metrics.json             # Evaluation metrics
│   └── decision_threshold.json  # Decision threshold (default 0.5)
├── chroma_data/                 # ChromaDB persistent store (auto-created)
├── logs/
│   └── queries.jsonl            # Append-only query log (auto-created)
├── notebooks/                   # Training and exploration notebooks
├── .env.example                 # Environment variable template
├── requirements-backend.txt     # Runtime Python dependencies
├── requirements.txt             # Full ML/notebook dependencies
├── Dockerfile                   # Backend container image
└── docker-compose.yml           # Backend + frontend services
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- A [Gemini API key](https://aistudio.google.com/app/apikey)
- The `twcs_raw.parquet` dataset file (place in `dataset/processed/`)

### 1. Clone and configure

```bash
git clone <repo-url>
cd DecisionAgent
cp .env.example .env
```

Edit `.env` and set your API key:

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

### 2. Start the backend

```bash
python -m venv .venv
source .venv/Scripts/activate        # Windows
# source .venv/bin/activate          # macOS / Linux

pip install -r requirements-backend.txt
uvicorn app.main:app --reload --port 8000
```

Backend is now running at `http://localhost:8000`.  
Interactive API docs: `http://localhost:8000/docs`

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend is now at `http://localhost:5173`. Vite proxies all API calls to the backend automatically.

### 4. Ingest the dataset

Before RAG queries work, you need to embed and store conversation threads in ChromaDB. From the Swagger UI at `/docs` or with curl:

```bash
# Ingest 10,000 threads (takes ~15 minutes — embeds in batches of 500)
curl -X POST "http://localhost:8000/ingest/threads?limit=10000&fresh=true"

# Or ingest all ~500K threads (takes several hours)
curl -X POST "http://localhost:8000/ingest/threads?fresh=true"

# Or ingest only one brand, e.g. AmazonHelp
curl -X POST "http://localhost:8000/ingest/threads?brand=AmazonHelp&limit=5000"
```

The response shows how many threads were built and chunks stored:

```json
{
  "threads_built": 10000,
  "chunks_stored": 11243,
  "brand_filter": null,
  "max_chars": 4000,
  "split_chunks": 1243
}
```

---

## Using the App

### Customer Support mode

Enter a question a customer might ask a brand (e.g. *"My package hasn't arrived and it's been two weeks"*). Optionally filter by brand handle (e.g. `AmazonHelp`, `AppleSupport`, `NikeSupport`).

The app calls both `/ask/rag` and `/ask` in parallel and shows:

- **RAG answer** — grounded exclusively in real past conversations, with similarity scores and source thread IDs
- **Direct LLM answer** — Gemini answering from general knowledge
- **Latency bar chart** — visual comparison of response times
- **Comparison table** — RAG vs Direct across sources cited, latency, cost, and grounding quality
- **Recommendation** — when to use each approach in production

The RAG prompt enforces strict rules: the LLM will cite specific conversations by number and refuse to answer if the retrieved context doesn't cover the question.

### Priority Predictor mode

Enter a support ticket text (e.g. *"MY ACCOUNT IS LOCKED AND I NEED IT FIXED NOW!!!"*). The app calls both `/priority/ml` and `/priority/llm` in parallel and shows:

- **ML prediction** — LightGBM classifier decision (Urgent / Normal) with confidence %
- **LLM prediction** — Gemini zero-shot classification with explanation
- **Agreement banner** — green if both agree, red if they disagree
- **Confidence bar chart** and **latency bar chart**
- **Comparison table** — ML vs LLM across test accuracy, latency, cost per call, and interpretability
- **Production recommendation** — ML for high-volume throughput, LLM for edge-case validation

### Logs page

Visit `http://localhost:5173/logs` to see all past queries with stats (total queries, per-type counts, average latency, cumulative cost), type filters, and expandable full JSON entries.

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/ask` | POST | Direct LLM answer from general knowledge |
| `/ask/rag` | POST | RAG answer grounded in retrieved threads |
| `/search` | GET | Search vector store without LLM |
| `/priority/ml` | POST | Urgency prediction via LightGBM |
| `/priority/llm` | POST | Urgency prediction via Gemini zero-shot |
| `/ingest` | POST | Ingest files from knowledge directory |
| `/ingest/threads` | POST | Ingest Twitter threads from parquet |
| `/embed` | POST | Pairwise semantic similarity explorer |
| `/store/inspect` | GET | Inspect stored chunks |
| `/store/sources` | GET | List unique sources in vector store |
| `/store/logs` | GET | Fetch recent query logs |
| `/store/metrics` | GET | ML model evaluation metrics |

**Request body** for `/ask`, `/ask/rag`, `/priority/ml`, `/priority/llm`:
```json
{ "text": "your customer question or ticket text" }
```

`/ask/rag` also accepts an optional `brand` query parameter to filter retrieved chunks.

Full interactive docs available at `http://localhost:8000/docs`.

---

## ML Model

The priority classifier is a LightGBM binary model trained on the Twitter customer support dataset.

**Feature set (20 features):**

| Category | Features |
|---|---|
| Text stats | `char_len`, `word_len`, `avg_word_len`, `unique_ratio`, `caps_ratio` |
| Punctuation | `exclaim_count`, `question_count`, `consecutive_punct`, `ellipsis` |
| Social | `mention_count`, `hashtag_count`, `url_count` |
| Keywords | `has_urgency_kw`, `has_negative_word`, `has_money_term`, `has_time_pressure` |
| Sentiment | `vader_neg`, `vader_neu`, `vader_pos`, `vader_compound` |

**Evaluation metrics:**

| Metric | Score |
|---|---|
| Accuracy | 99.66% |
| F1 (urgent) | 99.66% |
| Precision | 99.997% |
| Recall | 99.32% |
| ROC-AUC | 99.99% |
| Mean Latency | ~70 ms |
| Cost | $0.00/call |

The model is loaded once at startup and cached for the lifetime of the process. The decision threshold is stored separately in `models/decision_threshold.json` and can be tuned without retraining.

---

## RAG Pipeline

The Retrieval-Augmented Generation pipeline turns the 2.8M-tweet dataset into searchable semantic memory.

**Ingestion flow:**

```
twcs_raw.parquet
     │
     ▼
twitter_loader.py          Build dialogue threads from tweet graph
     │                     Root = null parent; walk response_tweet_id chain
     │                     Render as "CUSTOMER (handle): text\nBRAND (handle): text"
     ▼
thread_chunker.py          Split threads > 4000 chars at message boundaries
     │                     Recursively halves until all chunks fit
     ▼
embedder.py                Call Gemini gemini-embedding-001
     │                     Batch size 100, retry with exponential backoff
     │                     Returns 3072-dim vectors
     ▼
store.py                   Upsert into ChromaDB
                           Cosine distance metric
                           Batch size 500 (hard limit: 5461)
                           Metadata: source, chunk_index, brand, thread_id, n_messages
```

**Query flow:**

```
User question
     │
     ▼
embedder.py                Embed question (3072-dim vector)
     │
     ▼
store.py search()          ChromaDB cosine similarity search
     │                     Returns top-5 chunks with distances
     │                     Optional brand metadata filter
     ▼
grounded_answer.py         System prompt with strict rules:
     │                     • Answer only from provided conversations
     │                     • Cite sources by number
     │                     • Fixed fallback if context is insufficient
     ▼
Gemini 2.5 Flash           Generate grounded answer
```

---

## LLM Provider Configuration

The app supports three LLM providers. Switch by setting `LLM_PROVIDER` in `.env`.

**Gemini (default):**
```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

**OpenAI:**
```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

**Azure OpenAI:**
```dotenv
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
```

---

## Docker Deployment

```bash
cp .env.example .env
# Fill in GEMINI_API_KEY

docker compose up --build
```

This starts two services:

- **backend** on internal port 8000 (FastAPI)
- **frontend** on public port **8080** (Nginx serving React SPA)

Visit `http://localhost:8080`.

Volumes persist across container rebuilds:
- `chroma-data` → ChromaDB index (you don't need to re-ingest after `docker compose restart`)
- `logs` → query log JSONL

To wipe the vector store and start fresh:
```bash
docker compose down -v
docker compose up
```

---

## Configuration Reference

All settings live in `.env` (loaded by `app/config.py`):

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | LLM backend: `gemini`, `openai`, or `azure` |
| `GEMINI_API_KEY` | — | Required for Gemini provider |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Chat model for answers and priority |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | Embedding model |
| `CHROMA_PATH` | `./chroma_data` | ChromaDB persistent store directory |
| `LOGS_DIR` | `./logs` | Query log directory |
| `TWCS_PARQUET_PATH` | `./dataset/processed/twcs_raw.parquet` | Twitter dataset |
| `THREAD_MAX_CHARS` | `4000` | Max chars per thread chunk before splitting |
| `THREAD_MIN_MESSAGES` | `2` | Drop threads with fewer messages than this |
| `THREAD_INGEST_LIMIT` | `None` | Max threads to ingest (omit for all) |
| `RAG_TOP_K` | `5` | Number of chunks retrieved per query |
| `DEFAULT_CHUNK_SIZE` | `500` | Chars per chunk for file-based ingestion |
| `DEFAULT_CHUNK_OVERLAP` | `50` | Overlap between consecutive chunks |
| `CORS_ORIGINS` | `localhost:5173,...` | Allowed CORS origins |

---

## Development Notes

**Auto-reload:** `uvicorn --reload` watches for file changes and restarts the worker. During a long-running ingest request, a file save can cause a reload mid-flight. If the ingest fails partway through, re-run it with `fresh=false` to resume from where it left off (upserts are idempotent).

**ChromaDB limits:** The hard limit per upsert call is 5,461 items. The store module batches at 500 to stay safely below this. The ingest router also embeds and stores in batches of 500 to avoid accumulating all embeddings in memory.

**Cost tracking:** All Gemini calls record input/output token counts and estimated USD cost (0.075 $/M input, 0.30 $/M output for Gemini 2.5 Flash). These are written to `logs/queries.jsonl` and surfaced on the logs page.

**Re-ingesting a brand:** To refresh a specific brand without wiping the whole store:
```bash
# There is no partial-delete API — use fresh=true to wipe and re-ingest the brand
curl -X POST "http://localhost:8000/ingest/threads?brand=AmazonHelp&limit=5000&fresh=true"
```

---

## Dependencies

**Backend (`requirements-backend.txt`):**

| Package | Version | Purpose |
|---|---|---|
| fastapi | 0.115.6 | Web framework |
| uvicorn | 0.32.1 | ASGI server |
| chromadb | 0.5.23 | Vector store |
| google-genai | 1.5.0 | Gemini LLM + embeddings |
| openai | 1.57.0 | OpenAI / Azure LLM + embeddings |
| pandas + pyarrow | 2.2.3 / 18.1.0 | Parquet reading |
| scikit-learn | 1.5.2 | ML pipeline |
| lightgbm | 4.5.0 | Priority classifier |
| vaderSentiment | 3.3.2 | Sentiment features |
| nltk | 3.9.1 | NLP utilities |
| python-dotenv | 1.0.1 | Environment config |

**Frontend:**

| Package | Version | Purpose |
|---|---|---|
| react + react-dom | 18.3.1 | UI framework |
| react-router-dom | 7.14.2 | Client-side routing (/logs page) |
| recharts | 3.8.1 | Bar charts (latency, confidence) |
| vite | 6.x | Dev server + build tool |
