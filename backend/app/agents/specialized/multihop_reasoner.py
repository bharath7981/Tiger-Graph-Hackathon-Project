"""Specialized Multi-Hop Reasoning Agent for synthesizing evidence into grounded answers."""

import time
from typing import Any, Dict, List
from backend.app.agents.specialized.base import BaseSpecializedAgent, AgentResult
from backend.app.services.llm_provider import llm_provider
from backend.app.services.evidence import validate_citations, compute_groundedness_score
from backend.app.core.logging import logger


class MultiHopReasoningAgent(BaseSpecializedAgent):
    """Specialized agent synthesizing multi-hop graph traversals and text evidence into verified grounded answers."""

    def __init__(self):
        super().__init__(name="MultiHopReasoningAgent")

    def run(self, params: Dict[str, Any]) -> AgentResult:
        start_time = time.perf_counter()
        question = params.get("question", "")
        evidence = params.get("evidence", [])
        retrieved_chunks = params.get("retrieved_chunks", [])
        citations = list(set(params.get("citations", [])))

        # Compile formatted context
        context_parts: List[str] = []

        # Graph facts
        if evidence:
            context_parts.append("### Structured Graph Evidence:")
            for idx, ev in enumerate(evidence, 1):
                claim = ev.get("claim", str(ev))
                doc_id = ev.get("document_id")
                tag = f" [{doc_id}]" if doc_id else ""
                context_parts.append(f"{idx}. {claim}{tag}")

        # Text chunks
        if retrieved_chunks:
            context_parts.append("\n### Retrieved Document Context:")
            for idx, ch in enumerate(retrieved_chunks, 1):
                doc_id = ch.get("document_id") or ch.get("metadata", {}).get("document_id", "Unknown")
                citations.append(doc_id)
                context_parts.append(f"[{doc_id}] {ch.get('text', '')}")

        context_str = "\n".join(context_parts)
        unique_citations = sorted(list(set(citations)))

        # Prompt
        system_prompt = (
            "You are an expert Olympic Games research agent. Answer the question using ONLY the provided "
            "structured graph evidence and document context. Every factual assertion must be attributed "
            "with a bracketed citation tag like [Q12345] matching the source document. If the evidence is "
            "insufficient or incomplete, state clearly what is known and what cannot be determined."
        )

        user_prompt = (
            f"Question: {question}\n\n"
            f"Verified Evidence & Sources:\n{context_str}\n\n"
            "Formulate a precise, grounded answer with explicit bracketed citations:"
        )

        llm_resp = llm_provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.0,
            max_tokens=500,
        )

        answer = llm_resp.text.strip()
        latency = (time.perf_counter() - start_time) * 1000.0

        # Validate citations
        valid_cites, hall_cites = validate_citations(answer, unique_citations)
        evidence_texts = [ev.get("claim", "") for ev in evidence] + [ch.get("text", "") for ch in retrieved_chunks]
        groundedness = compute_groundedness_score(answer, evidence_texts)

        summary = (
            f"Generated multi-hop answer ({len(answer.split())} words, {len(valid_cites)} citations, "
            f"groundedness: {groundedness*100:.1f}%)"
        )

        return AgentResult(
            agent_name=self.name,
            status="success",
            data={
                "answer": answer,
                "citations": valid_cites,
                "hallucinated_citations": hall_cites,
                "groundedness": groundedness,
            },
            summary=summary,
            evidence_ids=valid_cites,
            latency_ms=round(latency, 2),
            tokens=llm_resp.total_tokens,
        )


multihop_reasoning_agent = MultiHopReasoningAgent()
