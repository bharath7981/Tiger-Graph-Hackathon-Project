"""Baseline RAG Pipeline implementation."""

import re
import time
from typing import Any, Dict, List, Optional
from backend.app.core.logging import logger
from backend.app.models.rag import RAGResult, RetrievedChunk
from backend.app.ingestion.vector_store import vector_store
from backend.app.services.llm_provider import llm_provider, LLMResponse


SYSTEM_PROMPT = """You are a precise, fact-based research assistant answering questions using only the retrieved evidence provided.

Strict Rules:
1. Answer using ONLY the retrieved evidence. Do NOT assume, extrapolate, or invent unsupported facts.
2. Cite your sources using the document title or ID in brackets, e.g., [Doc ID: Q12345] or [Title].
3. If the retrieved evidence is insufficient, ambiguous, or missing the answer, you MUST state:
   "Insufficient evidence to answer confidently."
4. Be direct, concise, and accurate."""


class BaselineRAG:
    """Baseline vector similarity-based RAG pipeline."""

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    def build_context(self, retrieved_chunks: List[RetrievedChunk]) -> str:
        """Formats retrieved chunks into structured context text."""
        if not retrieved_chunks:
            return "No relevant documents found."

        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, start=1):
            context_parts.append(
                f"[Chunk {i}] Document: {chunk.title} | Doc ID: {chunk.document_id}\n{chunk.text.strip()}\n"
            )
        return "\n---\n".join(context_parts)

    def extract_citations(self, answer: str, retrieved_chunks: List[RetrievedChunk]) -> List[str]:
        """Extracts cited document IDs and titles from the LLM answer."""
        citations = set()

        # Look for explicit [Doc ID: ...] or [Qxxxx]
        doc_id_matches = re.findall(r"\[(?:Doc ID:\s*)?(Q\d+)\]", answer, re.IGNORECASE)
        for doc_id in doc_id_matches:
            citations.add(doc_id.upper())

        # Check if retrieved document IDs or titles are explicitly referenced
        for chunk in retrieved_chunks:
            if chunk.document_id in answer:
                citations.add(chunk.document_id)
            elif chunk.title.lower() in answer.lower():
                citations.add(chunk.document_id)

        # Fallback: if answer is grounded and retrieved chunks exist, list top chunk doc_ids
        if not citations and "insufficient evidence" not in answer.lower():
            for c in retrieved_chunks[:2]:
                citations.add(c.document_id)

        return sorted(list(citations))

    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        question_id: Optional[str] = None,
        ground_truth: Optional[List[str]] = None,
    ) -> RAGResult:
        """Executes the baseline RAG pipeline for a given question.
        
        Args:
            question: Natural language query string.
            top_k: Number of chunks to retrieve (default: self.top_k).
            question_id: Optional tracking identifier.
            ground_truth: Optional expected canonical answers.
            
        Returns:
            Structured RAGResult with answer, citations, tokens, and latency metrics.
        """
        k = top_k or self.top_k
        pipeline_start = time.perf_counter()

        # 1. Vector Retrieval
        retrieval_start = time.perf_counter()
        raw_results = vector_store.similarity_search(query=question, top_k=k)
        retrieval_latency = (time.perf_counter() - retrieval_start) * 1000.0

        # Transform to RetrievedChunk models
        retrieved_chunks = [
            RetrievedChunk(
                chunk_id=r["chunk_id"],
                document_id=r["metadata"].get("document_id", ""),
                title=r["metadata"].get("title", ""),
                text=r["text"],
                score=r["score"],
                source=r["metadata"].get("source"),
            )
            for r in raw_results
        ]

        # 2. Context Construction
        context_str = self.build_context(retrieved_chunks)
        user_prompt = (
            f"=== RETRIEVED CONTEXT ===\n{context_str}\n=== END OF CONTEXT ===\n\n"
            f"Question: {question}\nAnswer:"
        )

        # 3. LLM Generation
        llm_start = time.perf_counter()
        llm_resp: LLMResponse = llm_provider.generate(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
        )
        llm_latency = (time.perf_counter() - llm_start) * 1000.0
        total_latency = (time.perf_counter() - pipeline_start) * 1000.0

        # 4. Citation and Confidence Analysis
        answer_text = llm_resp.text.strip()
        citations = self.extract_citations(answer_text, retrieved_chunks)

        is_insufficient = "insufficient evidence" in answer_text.lower()
        if is_insufficient:
            confidence = 0.0
        elif retrieved_chunks:
            # Scaled confidence based on top retrieval scores
            top_score = max(c.score for c in retrieved_chunks)
            confidence = round(min(1.0, max(0.1, top_score)), 3)
        else:
            confidence = 0.0

        # Optional Ground Truth Verification
        is_exact = None
        if ground_truth:
            norm_ans = answer_text.lower()
            is_exact = any(gt.lower() in norm_ans for gt in ground_truth)

        return RAGResult(
            question_id=question_id,
            question=question,
            answer=answer_text,
            retrieved_chunks=retrieved_chunks,
            citations=citations,
            input_tokens=llm_resp.input_tokens,
            output_tokens=llm_resp.output_tokens,
            total_tokens=llm_resp.total_tokens,
            latency_ms=round(total_latency, 2),
            retrieval_latency_ms=round(retrieval_latency, 2),
            llm_latency_ms=round(llm_latency, 2),
            confidence=confidence,
            ground_truth=ground_truth,
            is_exact_match=is_exact,
            metadata={"top_k": k, "provider": llm_resp.provider},
        )


# Global singleton instance
baseline_rag = BaselineRAG()
