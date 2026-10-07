"""Specialized Conflict Resolution Agent for adjudicating disputed facts and medal reallocations."""

import time
from typing import Any, Dict, List
from backend.app.agents.specialized.base import BaseSpecializedAgent, AgentResult
from backend.app.services.conflict_resolution import conflict_service
from backend.app.models.temporal import CompetingClaim
from backend.app.core.logging import logger


class ConflictResolutionAgent(BaseSpecializedAgent):
    """Specialized agent to detect contradictory claims, rank source authority, and resolve temporal reallocations."""

    def __init__(self):
        super().__init__(name="ConflictResolutionAgent")

    def run(self, params: Dict[str, Any]) -> AgentResult:
        start_time = time.perf_counter()
        question = params.get("question", "")
        evidence = params.get("evidence", [])
        retrieved_chunks = params.get("retrieved_chunks", [])
        entity_name = params.get("entity_name", "Olympic Event")

        # 1. Collect all textual passages
        passages: List[str] = []
        for ev in evidence:
            passages.append(ev.get("claim", "") or ev.get("fact", ""))
        for ch in retrieved_chunks:
            passages.append(ch.get("text", ""))

        combined_text = "\n".join(passages)

        try:
            # 2. Extract competing claims
            claims = conflict_service.extract_claims_from_text(combined_text)

            # 3. Adjudicate and resolve
            report = conflict_service.resolve_conflicts(claims, entity_name=entity_name)
            latency = (time.perf_counter() - start_time) * 1000.0

            summary = (
                f"Conflict Resolution: {'CONFLICT DETECTED (' + report.conflict_type + ')' if report.has_conflict else 'NO CONFLICT'}. "
                f"Resolved: {report.resolved_claim.value if report.resolved_claim else 'N/A'} "
                f"(Uncertainty: {report.residual_uncertainty*100:.1f}%)"
            )

            return AgentResult(
                agent_name=self.name,
                status="success",
                data={
                    "has_conflict": report.has_conflict,
                    "conflict_type": report.conflict_type,
                    "resolved_claim": report.resolved_claim.model_dump() if report.resolved_claim else None,
                    "resolution_rationale": report.resolution_rationale,
                    "residual_uncertainty": report.residual_uncertainty,
                    "competing_claims": [c.model_dump() for c in report.competing_claims],
                },
                summary=summary,
                latency_ms=round(latency, 2),
                tokens=40 + len(combined_text.split()[:200]),
            )

        except Exception as e:
            logger.error(f"ConflictResolutionAgent failed: {e}")
            return AgentResult(
                agent_name=self.name,
                status="error",
                error=str(e),
                latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )


conflict_resolution_agent = ConflictResolutionAgent()
