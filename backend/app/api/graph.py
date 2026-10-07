"""GraphRAG and Knowledge Graph inspection API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.models.graphrag import GraphRAGResult, EntityDetail, NeighborDetail
from backend.app.pipelines.graphrag import tigergraph_rag
from backend.app.graph.client import graph_client
from backend.app.core.logging import logger

router = APIRouter(tags=["GraphRAG"])


class GraphRAGQueryRequest(BaseModel):
    question: str = Field(..., description="Query prompt text")
    question_id: Optional[str] = Field(default=None, description="Optional question tracking identifier")


@router.post("/graphrag/query", response_model=GraphRAGResult)
def query_graphrag(req: GraphRAGQueryRequest) -> GraphRAGResult:
    """Executes deterministic GraphRAG pipeline on a question."""
    try:
        result = tigergraph_rag.query(
            question=req.question,
            question_id=req.question_id,
        )
        return result
    except Exception as e:
        logger.error(f"Error querying GraphRAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/entities/{entity_id}", response_model=EntityDetail)
def get_graph_entity(entity_id: str) -> EntityDetail:
    """Inspects a specific node/entity in the knowledge graph."""
    entity = graph_client.get_vertex(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found in knowledge graph.")
    return entity


@router.get("/graph/neighbors/{entity_id}", response_model=List[NeighborDetail])
def get_graph_neighbors(entity_id: str) -> List[NeighborDetail]:
    """Inspects neighboring nodes and connecting edges for a graph entity."""
    # Check existence
    entity = graph_client.get_vertex(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found in knowledge graph.")
    neighbors = graph_client.get_neighbors(entity_id)
    return neighbors
