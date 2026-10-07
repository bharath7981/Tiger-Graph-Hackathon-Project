"""Document and chunk data models."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DocumentRecord(BaseModel):
    """Normalized document model for corpus items."""
    document_id: str = Field(..., description="Unique document ID (e.g. Wikidata QID)")
    source: str = Field(..., description="Source URL or filename")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Full text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")


class ChunkRecord(BaseModel):
    """Normalized chunk model for vector store indexing."""
    chunk_id: str = Field(..., description="Unique chunk ID")
    document_id: str = Field(..., description="Parent document ID")
    text: str = Field(..., description="Text content of the chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
