"""Agentic GraphRAG API endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.agents.graph import run_agentic_investigation
from backend.app.core.logging import logger

router = APIRouter(prefix="/agentic", tags=["Agentic GraphRAG"])


class AgenticQueryRequest(BaseModel):
    question: str = Field(..., description="Query prompt text")
    question_id: Optional[str] = Field(default=None, description="Optional question tracking identifier")
    max_iterations: int = Field(default=6, ge=1, le=15, description="Maximum agent iteration ceiling")
    token_budget: int = Field(default=8000, ge=500, le=50000, description="Token consumption budget")


class AgenticQueryResponse(BaseModel):
    question_id: Optional[str] = None
    question: str
    answer: str
    confidence: float
    citations: List[str] = Field(default_factory=list)
    trace: List[Dict[str, Any]] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    agents_used: List[str] = Field(default_factory=list)
    steps: int
    tokens: int
    latency_ms: float


@router.post("/query", response_model=AgenticQueryResponse)
def query_agentic(req: AgenticQueryRequest) -> AgenticQueryResponse:
    """Executes adaptive LangGraph Agentic GraphRAG investigation."""
    try:
        result = run_agentic_investigation(
            question=req.question,
            question_id=req.question_id,
            max_iterations=req.max_iterations,
            token_budget=req.token_budget,
        )
        return AgenticQueryResponse(**result)
    except Exception as e:
        logger.error(f"Agentic investigation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
