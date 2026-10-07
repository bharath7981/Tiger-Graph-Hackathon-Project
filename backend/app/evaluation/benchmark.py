"""Comparative Benchmark Engine across RAG, GraphRAG, and Agentic GraphRAG."""

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.logging import logger
from backend.app.ingestion.loader import load_questions_from_jsonl
from backend.app.pipelines.rag import baseline_rag
from backend.app.pipelines.graphrag import tigergraph_rag
from backend.app.agents.graph import run_agentic_investigation
from backend.app.evaluation.metrics import evaluate_prediction
from backend.app.evaluation.classifier import classify_question_complexity


class BenchmarkConfig(BaseModel):
    questions_file: str = "questions/eval_public.jsonl"
    limit: int = 10
    output_dir: str = "evaluation/results"
    pipelines: List[str] = Field(default_factory=lambda: ["rag", "graphrag", "agentic"])


class BenchmarkEngine:
    """Orchestrates comprehensive comparative benchmarking across all 3 paradigms."""

    def __init__(self, config: Optional[BenchmarkConfig] = None):
        self.config = config or BenchmarkConfig()

    def run_benchmark(
        self,
        limit: Optional[int] = None,
        pipelines: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Executes full benchmark evaluation across configured questions and pipelines."""
        run_limit = limit or self.config.limit
        active_pipelines = pipelines or self.config.pipelines

        # Load questions
        q_path = Path(self.config.questions_file)
        if not q_path.exists():
            raise FileNotFoundError(f"Evaluation questions file not found: {q_path}")

        loaded = load_questions_from_jsonl(str(q_path))
        questions = loaded.get("public", [])[:run_limit]

        logger.info(f"Starting benchmark evaluation on {len(questions)} questions across {active_pipelines}")

        results: List[Dict[str, Any]] = []

        for idx, q in enumerate(questions, 1):
            q_id = q.question_id
            q_text = q.question
            gold_truth = q.ground_truth
            gold_docs = q.metadata.get("gold_doc_ids", [])
            qtype = q.metadata.get("qtype", "unknown")

            # Complexity classification
            complexity = classify_question_complexity(q_text, qtype)

            record: Dict[str, Any] = {
                "question_id": q_id,
                "question": q_text,
                "question_type": qtype,
                "complexity": complexity,
                "gold_document_ids": gold_docs,
                "ground_truth": gold_truth,
                "pipelines": {},
            }

            # 1. Baseline RAG
            if "rag" in active_pipelines:
                try:
                    rag_res = baseline_rag.query(
                        question=q_text,
                        question_id=q_id,
                        ground_truth=gold_truth,
                    )
                    record["pipelines"]["rag"] = {
                        "answer": rag_res.answer,
                        "citations": rag_res.citations,
                        "metrics": evaluate_prediction(
                            prediction=rag_res.answer,
                            citations=rag_res.citations,
                            ground_truth=gold_truth,
                            gold_document_ids=gold_docs,
                            latency_ms=rag_res.latency_ms,
                            tokens=rag_res.total_tokens,
                        ),
                    }
                except Exception as e:
                    logger.error(f"RAG failed on {q_id}: {e}")
                    record["pipelines"]["rag"] = {"error": str(e)}

            # 2. GraphRAG
            if "graphrag" in active_pipelines:
                try:
                    graph_res = tigergraph_rag.query(
                        question=q_text,
                        question_id=q_id,
                        ground_truth=gold_truth,
                    )
                    record["pipelines"]["graphrag"] = {
                        "answer": graph_res.answer,
                        "citations": graph_res.citations,
                        "metrics": evaluate_prediction(
                            prediction=graph_res.answer,
                            citations=graph_res.citations,
                            ground_truth=gold_truth,
                            gold_document_ids=gold_docs,
                            latency_ms=graph_res.latency_ms,
                            tokens=graph_res.total_tokens,
                        ),
                    }
                except Exception as e:
                    logger.error(f"GraphRAG failed on {q_id}: {e}")
                    record["pipelines"]["graphrag"] = {"error": str(e)}

            # 3. Agentic GraphRAG
            if "agentic" in active_pipelines:
                try:
                    agent_res = run_agentic_investigation(
                        question=q_text,
                        question_id=q_id,
                    )
                    record["pipelines"]["agentic"] = {
                        "answer": agent_res["answer"],
                        "citations": agent_res["citations"],
                        "steps": agent_res["steps"],
                        "tools_used": agent_res["tools_used"],
                        "agents_used": agent_res["agents_used"],
                        "metrics": evaluate_prediction(
                            prediction=agent_res["answer"],
                            citations=agent_res["citations"],
                            ground_truth=gold_truth,
                            gold_document_ids=gold_docs,
                            latency_ms=agent_res["latency_ms"],
                            tokens=agent_res["tokens"],
                        ),
                    }
                except Exception as e:
                    logger.error(f"Agentic GraphRAG failed on {q_id}: {e}")
                    record["pipelines"]["agentic"] = {"error": str(e)}

            results.append(record)

        # Compute Aggregates
        summary = self._compute_aggregates(results, active_pipelines)

        # Export outputs
        self._export_results(results, summary)

        return summary

    def _compute_aggregates(
        self,
        results: List[Dict[str, Any]],
        pipelines: List[str],
    ) -> Dict[str, Any]:
        """Calculates macro metrics and complexity breakdown across all evaluated runs."""
        total_questions = len(results)
        pipeline_stats: Dict[str, Any] = {}

        for p in pipelines:
            runs = [r["pipelines"].get(p, {}).get("metrics") for r in results if p in r["pipelines"] and "metrics" in r["pipelines"][p]]
            if not runs:
                continue

            hit_rate = sum(1 for m in runs if m.get("citation_hit")) / len(runs)
            avg_precision = sum(m.get("citation_precision", 0.0) for m in runs) / len(runs)
            avg_recall = sum(m.get("citation_recall", 0.0) for m in runs) / len(runs)
            avg_latency = sum(m.get("latency_ms", 0.0) for m in runs) / len(runs)
            avg_tokens = sum(m.get("tokens", 0) for m in runs) / len(runs)

            pipeline_stats[p] = {
                "evaluated_count": len(runs),
                "gold_hit_rate": round(hit_rate, 4),
                "citation_precision": round(avg_precision, 4),
                "citation_recall": round(avg_recall, 4),
                "avg_latency_ms": round(avg_latency, 2),
                "avg_tokens": round(avg_tokens, 1),
            }

        # Breakdown by Question Type
        types_breakdown: Dict[str, Dict[str, Any]] = {}
        for r in results:
            qt = r.get("question_type", "other")
            if qt not in types_breakdown:
                types_breakdown[qt] = {"count": 0, "pipelines": {p: {"hits": 0, "tokens": 0, "latency": 0.0} for p in pipelines}}

            types_breakdown[qt]["count"] += 1
            for p in pipelines:
                m = r["pipelines"].get(p, {}).get("metrics")
                if m:
                    if m.get("citation_hit"):
                        types_breakdown[qt]["pipelines"][p]["hits"] += 1
                    types_breakdown[qt]["pipelines"][p]["tokens"] += m.get("tokens", 0)
                    types_breakdown[qt]["pipelines"][p]["latency"] += m.get("latency_ms", 0.0)

        # Final Summary structure
        summary = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_questions": total_questions,
            "pipelines_evaluated": pipelines,
            "overall_metrics": pipeline_stats,
            "question_type_breakdown": types_breakdown,
            "detailed_results": results,
        }

        return summary

    def _export_results(self, results: List[Dict[str, Any]], summary: Dict[str, Any]):
        """Persists benchmark summary JSON and comparative CSV."""
        out_dir = Path(self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # JSON Summary
        json_path = out_dir / "benchmark_summary.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved benchmark summary to {json_path}")

        # CSV Comparison
        csv_path = out_dir / "benchmark_comparison.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "question_id",
                "question_type",
                "complexity_level",
                "rag_hit",
                "rag_tokens",
                "rag_latency_ms",
                "graphrag_hit",
                "graphrag_tokens",
                "graphrag_latency_ms",
                "agentic_hit",
                "agentic_tokens",
                "agentic_latency_ms",
                "agentic_steps",
            ])

            for r in results:
                p_rag = r["pipelines"].get("rag", {}).get("metrics", {})
                p_graph = r["pipelines"].get("graphrag", {}).get("metrics", {})
                p_agent = r["pipelines"].get("agentic", {})
                p_agent_m = p_agent.get("metrics", {})

                writer.writerow([
                    r.get("question_id"),
                    r.get("question_type"),
                    r.get("complexity", {}).get("level", 1),
                    1 if p_rag.get("citation_hit") else 0,
                    p_rag.get("tokens", 0),
                    p_rag.get("latency_ms", 0.0),
                    1 if p_graph.get("citation_hit") else 0,
                    p_graph.get("tokens", 0),
                    p_graph.get("latency_ms", 0.0),
                    1 if p_agent_m.get("citation_hit") else 0,
                    p_agent_m.get("tokens", 0),
                    p_agent_m.get("latency_ms", 0.0),
                    p_agent.get("steps", 0),
                ])
        logger.info(f"Saved benchmark CSV comparison to {csv_path}")


benchmark_engine = BenchmarkEngine()
