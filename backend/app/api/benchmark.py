"""Benchmark and evaluation API endpoints."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.evaluation.benchmark import benchmark_engine
from backend.app.evaluation.value_analysis import generate_agentic_value_analysis
from backend.app.ingestion.loader import load_questions_from_jsonl
from backend.app.evaluation.classifier import classify_question_complexity
from backend.app.core.logging import logger

router = APIRouter(prefix="/benchmark", tags=["Benchmark & Evaluation"])


class BenchmarkRunRequest(BaseModel):
    limit: int = Field(default=5, ge=1, le=100, description="Number of questions to evaluate")
    pipelines: List[str] = Field(
        default_factory=lambda: ["rag", "graphrag", "agentic"],
        description="Pipelines to benchmark",
    )


@router.post("/run")
def run_benchmark_endpoint(req: BenchmarkRunRequest) -> Dict[str, Any]:
    """Executes comparative evaluation across RAG, GraphRAG, and Agentic GraphRAG."""
    try:
        summary = benchmark_engine.run_benchmark(
            limit=req.limit,
            pipelines=req.pipelines,
        )
        generate_agentic_value_analysis()
        return summary
    except Exception as e:
        logger.error(f"Benchmark execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
def get_benchmark_summary() -> Dict[str, Any]:
    """Returns the latest benchmark summary report."""
    summary_path = Path("evaluation/results/benchmark_summary.json")
    if not summary_path.exists():
        # Run default 5 questions if not yet executed
        try:
            summary = benchmark_engine.run_benchmark(limit=5)
            generate_agentic_value_analysis()
            return summary
        except Exception as e:
            raise HTTPException(status_code=404, detail="No benchmark results found. Run benchmark first.")

    with open(summary_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/questions")
def get_benchmark_questions(
    limit: int = Query(default=20, ge=1, le=150),
) -> List[Dict[str, Any]]:
    """Returns evaluation questions annotated with their 4-tier complexity classification."""
    q_file = Path("questions/eval_public.jsonl")
    if not q_file.exists():
        raise HTTPException(status_code=404, detail="Public questions file not found")

    loaded = load_questions_from_jsonl(str(q_file))
    questions = loaded.get("public", [])[:limit]

    out = []
    for q in questions:
        qtype = q.metadata.get("qtype", "unknown")
        complexity = classify_question_complexity(q.question, qtype)
        out.append({
            "question_id": q.question_id,
            "question": q.question,
            "question_type": qtype,
            "complexity": complexity,
            "ground_truth": q.ground_truth,
            "gold_document_ids": q.metadata.get("gold_doc_ids", []),
        })

    return out


@router.get("/value-analysis")
def get_value_analysis() -> Dict[str, Any]:
    """Returns the generated empirical Agentic Value Analysis markdown."""
    doc_path = Path("docs/AGENTIC_VALUE_ANALYSIS.md")
    if not doc_path.exists():
        generate_agentic_value_analysis()

    if doc_path.exists():
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"status": "ok", "markdown": content}
    else:
        raise HTTPException(status_code=404, detail="Value analysis document not found.")
