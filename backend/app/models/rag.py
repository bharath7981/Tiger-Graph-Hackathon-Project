"""RAG pipeline data models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """Represents a retrieved chunk with similarity score and metadata."""
    chunk_id: str
    document_id: str
    title: str
    text: str
    score: float
    source: Optional[str] = None


class RAGResult(BaseModel):
    """Structured result returned by the baseline RAG pipeline."""
    question_id: Optional[str] = None
    question: str
    answer: str
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    confidence: Optional[float] = None
    ground_truth: Optional[List[str]] = None
    is_exact_match: Optional[bool] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
