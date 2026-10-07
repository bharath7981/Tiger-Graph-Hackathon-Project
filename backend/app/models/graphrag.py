"""Data models for GraphRAG pipeline and graph inspection."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GraphPath(BaseModel):
    """Represents a traversed path in the knowledge graph."""
    source: str
    edge: str
    target: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEvidence(BaseModel):
    """Structured evidence fact retrieved from the graph with document attribution."""
    fact: str
    document_id: str
    entity_id: str
    entity_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphRAGResult(BaseModel):
    """Structured output from deterministic GraphRAG pipeline."""
    question_id: Optional[str] = None
    question: str
    answer: str
    entities: List[str] = Field(default_factory=list, description="Linked entities from question")
    graph_paths: List[str] = Field(default_factory=list, description="Human-readable traversed graph edges")
    evidence: List[GraphEvidence] = Field(default_factory=list, description="Attributed graph evidence facts")
    citations: List[str] = Field(default_factory=list, description="Source document IDs")
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    graph_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    confidence: Optional[float] = None
    ground_truth: Optional[List[str]] = None
    is_exact_match: Optional[bool] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EntityDetail(BaseModel):
    """Detailed view of a graph entity."""
    entity_id: str
    entity_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class NeighborDetail(BaseModel):
    """Neighboring node with connecting relationship."""
    neighbor_id: str
    neighbor_type: str
    edge_type: str
    direction: str = "outgoing"  # outgoing | incoming
    edge_properties: Dict[str, Any] = Field(default_factory=dict)
    neighbor_properties: Dict[str, Any] = Field(default_factory=dict)
