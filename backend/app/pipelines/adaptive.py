"""Adaptive Query Router and Pareto-Optimal Dispatcher.

Operationalizes the Agentic Value Analysis Decision Matrix by inspecting query complexity
and dispatching to the Pareto-optimal retrieval paradigm (Baseline RAG, TigerGraph GraphRAG,
or Agentic GraphRAG) while tracking latency and token savings.
"""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.logging import logger
from backend.app.evaluation.classifier import classify_question_complexity
from backend.app.pipelines.rag import baseline_rag
from backend.app.pipelines.graphrag import tigergraph_rag
from backend.app.agents.graph import run_agentic_investigation


class AdaptiveResult(BaseModel):
    """Normalized response from the Adaptive Router."""
    question: str
    question_id: Optional[str] = None
    chosen_paradigm: str  # 'rag' | 'graphrag' | 'agentic'
    complexity_level: int  # 1, 2, 3, 4
    complexity_label: str
    routing_rationale: str
    is_conflict_suspected: bool = False

    # Execution performance
    answer: str
    citations: List[str] = Field(default_factory=list)
    actual_latency_ms: float
    actual_tokens: int

    # Economic & Efficiency metrics (vs blind agentic execution)
    reference_agentic_tokens: int = 512
    reference_agentic_latency_ms: float = 45.0
    tokens_saved: int
    latency_saved_ms: float
    cost_efficiency_multiplier: float

    # Raw pipeline payload
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class AdaptiveRouter:
    """Intelligent dispatcher selecting the optimal paradigm based on complexity tier."""

    CONFLICT_KEYWORDS = [
        "stripped",
        "doping",
        "reallocated",
        "disqualified",
        "tested positive",
        "retrospective",
        "overturned",
    ]

    def route_and_execute(
        self,
        question: str,
        question_id: Optional[str] = None,
        override_paradigm: Optional[str] = None,
    ) -> AdaptiveResult:
        """Analyzes question complexity, routes to optimal paradigm, and executes query."""
        q_lower = question.lower()
        classification = classify_question_complexity(question)
        complexity_level = classification["level"]
        complexity_label = classification["label"]

        # Detect conflict cues
        is_conflict = any(kw in q_lower for kw in self.CONFLICT_KEYWORDS)

        # Determine chosen paradigm
        if override_paradigm and override_paradigm.lower() in ["rag", "graphrag", "agentic"]:
            chosen_paradigm = override_paradigm.lower()
            rationale = f"Manual override to {chosen_paradigm.upper()} requested by user."
        elif is_conflict:
            chosen_paradigm = "agentic"
            rationale = "Retrospective conflict / doping dispute detected; routed to Agentic Swarm for conflict resolution."
        elif complexity_level == 1:
            chosen_paradigm = "rag"
            rationale = f"Level 1 Factoid: Routed to Baseline Vector RAG. Single-pass semantic lookup is optimal with zero agent overhead."
        elif complexity_level == 2:
            chosen_paradigm = "graphrag"
            rationale = f"Level 2 Relational: Routed to TigerGraph GraphRAG. Deterministic 1-hop traversal resolves entities in <20ms with minimal tokens."
        elif complexity_level in [3, 4]:
            chosen_paradigm = "agentic"
            rationale = f"Level {complexity_level} ({complexity_label}): Routed to LangGraph Agentic GraphRAG. Required dynamic multi-hop or aggregation reasoning."
        else:
            chosen_paradigm = "rag"
            rationale = "Default fallback to Baseline Vector RAG."

        logger.info(f"AdaptiveRouter: '{question[:50]}...' -> {chosen_paradigm.upper()} (Level {complexity_level})")

        start_time = time.time()
        answer = ""
        citations: List[str] = []
        actual_tokens = 0
        actual_latency_ms = 0.0
        raw_payload: Dict[str, Any] = {}

        if chosen_paradigm == "rag":
            rag_res = baseline_rag.query(question=question, question_id=question_id)
            answer = rag_res.answer
            citations = rag_res.citations
            actual_tokens = rag_res.total_tokens
            actual_latency_ms = rag_res.latency_ms
            raw_payload = rag_res.model_dump()

        elif chosen_paradigm == "graphrag":
            graph_res = tigergraph_rag.query(question=question, question_id=question_id)
            answer = graph_res.answer
            citations = graph_res.citations
            actual_tokens = graph_res.total_tokens
            actual_latency_ms = graph_res.latency_ms
            raw_payload = graph_res.model_dump()

        else:  # agentic
            agent_res = run_agentic_investigation(question=question, question_id=question_id)
            answer = agent_res.get("answer", "")
            citations = agent_res.get("citations", [])
            actual_tokens = agent_res.get("tokens", 0)
            actual_latency_ms = agent_res.get("latency_ms", round((time.time() - start_time) * 1000, 2))
            raw_payload = agent_res

        # Calculate efficiency savings relative to reference agentic run (512 tokens, 45ms)
        ref_tokens = 512
        ref_latency = 45.0
        
        if chosen_paradigm == "agentic":
            tokens_saved = 0
            latency_saved_ms = 0.0
            efficiency_mult = 1.0
        else:
            tokens_saved = max(0, ref_tokens - actual_tokens)
            latency_saved_ms = round(max(0.0, ref_latency - actual_latency_ms), 2)
            efficiency_mult = round(ref_tokens / max(1, actual_tokens), 2)

        return AdaptiveResult(
            question=question,
            question_id=question_id,
            chosen_paradigm=chosen_paradigm,
            complexity_level=complexity_level,
            complexity_label=complexity_label,
            routing_rationale=rationale,
            is_conflict_suspected=is_conflict,
            answer=answer,
            citations=citations,
            actual_latency_ms=round(actual_latency_ms, 2),
            actual_tokens=actual_tokens,
            reference_agentic_tokens=ref_tokens,
            reference_agentic_latency_ms=ref_latency,
            tokens_saved=tokens_saved,
            latency_saved_ms=latency_saved_ms,
            cost_efficiency_multiplier=efficiency_mult,
            raw_payload=raw_payload,
        )


adaptive_router = AdaptiveRouter()
