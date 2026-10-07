"""State definitions and trace models for LangGraph investigation agent."""

from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class TraceStep(BaseModel):
    """Structured record of a single action step in the investigation trace."""
    step_number: int
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    action: str
    tool: str
    agent: str = "Orchestrator"
    input_summary: str
    output_summary: str
    latency_ms: float = 0.0
    tokens: int = 0
    reason: str = ""
    evidence_ids: List[str] = Field(default_factory=list)


class InvestigationState(TypedDict, total=False):
    """Accumulated state across the LangGraph investigation loop."""
    question: str
    question_id: Optional[str]
    entities: List[str]
    sub_questions: List[str]
    evidence: List[Dict[str, Any]]
    retrieved_chunks: List[Dict[str, Any]]
    graph_results: List[Dict[str, Any]]
    citations: List[str]
    missing_information: List[str]
    contradictions: List[str]
    actions_taken: List[str]
    agents_used: List[str]
    tools_used: List[str]
    current_plan: str
    confidence: float
    iteration: int
    max_iterations: int
    token_budget: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    final_answer: Optional[str]
    status: str  # "investigating" | "sufficient" | "budget_exceeded" | "max_iterations" | "concluded"
    trace: List[Dict[str, Any]]
    next_action: Optional[Dict[str, Any]]
