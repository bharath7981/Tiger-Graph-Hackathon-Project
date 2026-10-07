"""Specialized Similarity Retrieval Agent for dense vector retrieval."""

import time
from typing import Any, Dict, List
from backend.app.agents.specialized.base import BaseSpecializedAgent, AgentResult
from backend.app.ingestion.vector_store import vector_store
from backend.app.core.logging import logger


class SimilarityRetrievalAgent(BaseSpecializedAgent):
    """Specialized agent to perform targeted dense semantic vector search over Olympic corpus chunks."""

    def __init__(self):
        super().__init__(name="SimilarityRetrievalAgent")

    def run(self, params: Dict[str, Any]) -> AgentResult:
        start_time = time.perf_counter()
        query = params.get("query", "")
        top_k = params.get("top_k", 4)

        if not query:
            return AgentResult(
                agent_name=self.name,
                status="error",
                error="Query string is required",
            )

        try:
            results = vector_store.similarity_search(query=query, top_k=top_k)

            evidence_ids: List[str] = []
            formatted_chunks: List[Dict[str, Any]] = []

            for r in results:
                meta = r.get("metadata", {})
                source_doc_id = meta.get("document_id", "Unknown")
                evidence_ids.append(source_doc_id)
                formatted_chunks.append({
                    "chunk_id": r.get("chunk_id", ""),
                    "document_id": source_doc_id,
                    "title": meta.get("title", ""),
                    "text": r.get("text", ""),
                    "score": r.get("score", 0.0),
                    "metadata": meta,
                })

            unique_doc_ids = sorted(list(set(evidence_ids)))
            latency = (time.perf_counter() - start_time) * 1000.0
            top_score = formatted_chunks[0]["score"] if formatted_chunks else 0.0
            summary = (
                f"Retrieved {len(formatted_chunks)} dense chunks "
                f"across {len(unique_doc_ids)} unique documents (top score: {top_score:.3f})"
            )

            return AgentResult(
                agent_name=self.name,
                status="success",
                data={
                    "chunks": formatted_chunks,
                    "retrieved_count": len(formatted_chunks),
                    "unique_documents": unique_doc_ids,
                },
                summary=summary,
                evidence_ids=unique_doc_ids,
                latency_ms=round(latency, 2),
                tokens=len(query.split()) + sum(len(c["text"].split()) for c in formatted_chunks),
            )

        except Exception as e:
            logger.error(f"SimilarityRetrievalAgent failed: {e}")
            return AgentResult(
                agent_name=self.name,
                status="error",
                error=str(e),
                latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )


similarity_retrieval_agent = SimilarityRetrievalAgent()
