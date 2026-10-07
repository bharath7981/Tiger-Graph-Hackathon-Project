"""RAG API endpoints."""

import json
import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.models.rag import RAGResult
from backend.app.pipelines.rag import baseline_rag
from backend.app.ingestion.loader import load_questions_from_jsonl
from backend.app.core.logging import logger

router = APIRouter(prefix="/rag", tags=["RAG"])


class RAGQueryRequest(BaseModel):
    question: str = Field(..., description="Query prompt text")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of chunks to retrieve")
    question_id: Optional[str] = Field(default=None, description="Optional question ID tracking")


# Question cache for evaluate endpoint
_CACHED_QUESTIONS = None


def get_cached_questions():
    global _CACHED_QUESTIONS
    if _CACHED_QUESTIONS is None:
        pub_path = "questions/eval_public.jsonl"
        hid_path = "questions/eval_hidden.jsonl"
        all_q = {}
        if os.path.exists(pub_path) or os.path.exists(hid_path):
            res = load_questions_from_jsonl(pub_path, hid_path)
            for q in res["public"] + res["hidden"]:
                all_q[q.question_id] = q
        _CACHED_QUESTIONS = all_q
    return _CACHED_QUESTIONS


@router.post("/query", response_model=RAGResult)
def query_rag(req: RAGQueryRequest) -> RAGResult:
    """Executes baseline RAG pipeline on a question."""
    try:
        result = baseline_rag.query(
            question=req.question,
            top_k=req.top_k,
            question_id=req.question_id,
        )
        return result
    except Exception as e:
        logger.error(f"Error querying RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate/{question_id}", response_model=RAGResult)
def evaluate_rag_question(question_id: str, top_k: int = 5) -> RAGResult:
    """Runs baseline RAG against a specific dataset question and stores results."""
    questions = get_cached_questions()
    if question_id not in questions:
        raise HTTPException(status_code=404, detail=f"Question '{question_id}' not found in dataset.")

    q_record = questions[question_id]
    result = baseline_rag.query(
        question=q_record.question,
        top_k=top_k,
        question_id=q_record.question_id,
        ground_truth=q_record.ground_truth,
    )

    # Save result under evaluation/results/rag/{question_id}.json
    results_dir = "evaluation/results/rag"
    os.makedirs(results_dir, exist_ok=True)
    out_file = os.path.join(results_dir, f"{question_id}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)

    logger.info(f"Evaluation result saved for {question_id} -> {out_file}")
    return result
