"""Specialized Evidence Evaluation Agent for coverage, sufficiency, and contradiction checking."""

import time
from typing import Any, Dict, List
from backend.app.agents.specialized.base import BaseSpecializedAgent, AgentResult
from backend.app.services.evidence import evaluate_evidence_intelligence
from backend.app.core.logging import logger


class EvidenceEvaluationAgent(BaseSpecializedAgent):
    """Specialized agent to assess evidence sufficiency, coverage, contradictions, and citation integrity."""

    def __init__(self):
        super().__init__(name="EvidenceEvaluationAgent")

    def run(self, params: Dict[str, Any]) -> AgentResult:
        start_time = time.perf_counter()
        question = params.get("question", "")
        evidence = params.get("evidence", [])
        retrieved_chunks = params.get("retrieved_chunks", [])

        # Gather all available document IDs
        available_docs = set()
        for ev in evidence:
            doc_id = ev.get("document_id")
            if doc_id:
                available_docs.add(doc_id)
        for chunk in retrieved_chunks:
            doc_id = chunk.get("document_id") or chunk.get("metadata", {}).get("document_id")
            if doc_id:
                available_docs.add(doc_id)

        # Consolidate evidence items
        consolidated = []
        for ev in evidence:
            consolidated.append({"source": "graph", "text": ev.get("claim", str(ev))})
        for ch in retrieved_chunks:
            consolidated.append({"source": "vector", "text": ch.get("text", "")})

        # Evaluate evidence intelligence
        report = evaluate_evidence_intelligence(
            question=question,
            answer="",  # Pre-generation coverage check
            evidence_items=consolidated,
            available_doc_ids=list(available_docs),
        )

        latency = (time.perf_counter() - start_time) * 1000.0
        confidence = round(min(1.0, report.coverage_score * 1.1), 2)
        is_sufficient = report.is_sufficient or (len(consolidated) >= 2 and report.coverage_score >= 0.5)

        summary = (
            f"Coverage: {report.coverage_score*100:.1f}%, Sufficient: {is_sufficient}, "
            f"Contradictions: {len(report.contradictions)}, Available Sources: {len(available_docs)}"
        )

        return AgentResult(
            agent_name=self.name,
            status="success",
            data={
                "coverage_score": report.coverage_score,
                "confidence": confidence,
                "is_sufficient": is_sufficient,
                "contradictions": report.contradictions,
                "missing_information": report.missing_aspects,
                "available_document_ids": list(available_docs),
            },
            summary=summary,
            evidence_ids=list(available_docs),
            latency_ms=round(latency, 2),
            tokens=35 + len(question.split()),
        )


evidence_evaluation_agent = EvidenceEvaluationAgent()
