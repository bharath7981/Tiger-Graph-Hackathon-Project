"""Adaptive Query Router API endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.pipelines.adaptive import adaptive_router, AdaptiveResult
from backend.app.evaluation.classifier import classify_question_complexity
from backend.app.core.logging import logger

router = APIRouter(prefix="/adaptive", tags=["Adaptive Router"])


class AdaptiveQueryRequest(BaseModel):
    question: str = Field(..., description="Query prompt text")
    question_id: Optional[str] = Field(default=None, description="Optional question tracking identifier")
    override_paradigm: Optional[str] = Field(default=None, description="Optional paradigm override ('rag', 'graphrag', 'agentic')")


class AdaptiveClassifyRequest(BaseModel):
    question: str = Field(..., description="Query prompt text")
    question_type: Optional[str] = Field(default="unknown", description="Optional question type hint")


class AdaptiveClassifyResponse(BaseModel):
    question: str
    level: int
    label: str
    recommended_pipeline: str
    justification: str
    is_conflict_suspected: bool


class AdaptiveQueryResponse(BaseModel):
    question: str
    question_id: Optional[str] = None
    chosen_paradigm: str
    complexity_level: int
    complexity_label: str
    routing_rationale: str
    is_conflict_suspected: bool
    answer: str
    citations: List[str] = Field(default_factory=list)
    actual_latency_ms: float
    actual_tokens: int
    reference_agentic_tokens: int
    reference_agentic_latency_ms: float
    tokens_saved: int
    latency_saved_ms: float
    cost_efficiency_multiplier: float
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


@router.post("/classify", response_model=AdaptiveClassifyResponse)
def classify_question(req: AdaptiveClassifyRequest) -> AdaptiveClassifyResponse:
    """Pre-flight check: analyzes query complexity tier and predicted routing without executing pipelines."""
    try:
        classification = classify_question_complexity(req.question, req.question_type or "unknown")
        q_lower = req.question.lower()
        is_conflict = any(kw in q_lower for kw in adaptive_router.CONFLICT_KEYWORDS)
        
        return AdaptiveClassifyResponse(
            question=req.question,
            level=classification["level"],
            label=classification["label"],
            recommended_pipeline=classification["recommended_pipeline"] if not is_conflict else "Agentic GraphRAG (Conflict Resolution)",
            justification=classification["justification"] if not is_conflict else "Query contains retrospective medal stripping/doping conflict cues.",
            is_conflict_suspected=is_conflict,
        )
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=AdaptiveQueryResponse)
def query_adaptive(req: AdaptiveQueryRequest) -> AdaptiveQueryResponse:
    """Classifies question complexity and dynamically routes to the Pareto-optimal pipeline."""
    try:
        res: AdaptiveResult = adaptive_router.route_and_execute(
            question=req.question,
            question_id=req.question_id,
            override_paradigm=req.override_paradigm,
        )
        return AdaptiveQueryResponse(**res.model_dump())
    except Exception as e:
        logger.error(f"Adaptive query routing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
