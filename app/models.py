# ============================================================
# Pydantic models — request/response schemas
# ============================================================

from pydantic import BaseModel


class Question(BaseModel):
    """A user question sent to the assistant."""
    question: str


class Answer(BaseModel):
    """A plain LLM answer — may or may not be grounded in context."""
    answer: str
    model: str
    grounded: bool = False


class ChunkInfo(BaseModel):
    """Metadata about a single chunk — used in API responses."""
    text: str
    source: str
    chunk_index: int


class IngestResponse(BaseModel):
    """Response from the /ingest endpoint — summarizes what was loaded."""
    files_processed: int
    total_chunks: int
    chunks_stored: int
    chunks: list[ChunkInfo]


class SearchResult(BaseModel):
    """A single search result from the vector store."""
    text: str
    source: str
    chunk_index: int
    distance: float


class SearchResponse(BaseModel):
    """Response from the /search endpoint."""
    query: str
    results: list[SearchResult]
    total_results: int


class StoredChunkInfo(BaseModel):
    """Detailed info about a stored chunk — for the /store/inspect endpoint."""
    id: str
    text: str
    source: str
    chunk_index: int
    embedding_preview: list[float] | None = None
    embedding_dimensions: int | None = None


class StoreInspectResponse(BaseModel):
    """Response from the /store/inspect endpoint."""
    total_stored: int
    sources: list[str]
    chunks: list[StoredChunkInfo]


class StoreSourcesResponse(BaseModel):
    """Response from the /store/sources endpoint — list of unique source filenames."""
    sources: list[str]


class EmbedRequest(BaseModel):
    """Request to embed texts for exploration."""
    texts: list[str]


class PairwiseDistance(BaseModel):
    """Distance between two embedded texts with a human-readable similarity label."""
    distance: float
    similarity: str


class EmbedResponse(BaseModel):
    """Response with pairwise distances between embedded texts."""
    distances: dict[str, PairwiseDistance]
    dimensions: int


# ---- Decision Intelligence schemas ----

class TicketRequest(BaseModel):
    """A raw support ticket text sent for analysis."""
    text: str


class RetrievedTicket(BaseModel):
    """A ticket retrieved from the vector store during RAG."""
    text: str
    source: str
    distance: float
    priority: str | None = None
    brand: str | None = None
    thread_id: str | None = None


class PlainAnswerResponse(BaseModel):
    """LLM answer with no retrieved context."""
    answer: str
    model: str
    latency_ms: float


class RAGAnswerResponse(BaseModel):
    """LLM answer grounded in retrieved similar tickets."""
    answer: str
    model: str
    latency_ms: float
    retrieved_tickets: list[RetrievedTicket]


class PriorityMLResponse(BaseModel):
    """Priority prediction from the trained ML classifier."""
    label: str
    confidence: float
    latency_ms: float
    model_available: bool


class PriorityLLMResponse(BaseModel):
    """Priority prediction from the LLM zero-shot classifier."""
    label: str
    confidence: float
    explanation: str
    model: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float


class CompareResponse(BaseModel):
    """Four-way comparison: plain LLM, RAG, ML priority, LLM priority."""
    query: str
    plain_answer: PlainAnswerResponse
    rag_answer: RAGAnswerResponse
    priority_ml: PriorityMLResponse
    priority_llm: PriorityLLMResponse
