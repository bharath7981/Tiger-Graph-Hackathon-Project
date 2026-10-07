"""CLI runner for deterministic GraphRAG pipeline."""

import argparse
import json
import os
import sys

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure root and backend in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "../../.."))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app.core.logging import logger
from backend.app.pipelines.graphrag import tigergraph_rag
from backend.app.ingestion.loader import load_questions_from_jsonl


def run_graphrag_cli(
    question_id: str = None,
    custom_question: str = None,
    limit: int = None,
    run_all: bool = False,
    results_dir: str = "evaluation/results/graphrag",
):
    """Executes GraphRAG against question or benchmark dataset."""
    os.makedirs(results_dir, exist_ok=True)
    pub_path = "questions/eval_public.jsonl"
    hid_path = "questions/eval_hidden.jsonl"
    questions_data = load_questions_from_jsonl(pub_path, hid_path)
    all_questions = {q.question_id: q for q in questions_data["public"] + questions_data["hidden"]}

    targets = []
    if question_id:
        if question_id not in all_questions:
            print(f"Error: Question ID '{question_id}' not found.")
            sys.exit(1)
        targets.append(all_questions[question_id])
    elif custom_question:
        from backend.app.models.question import QuestionRecord
        targets.append(
            QuestionRecord(
                question_id="custom",
                question=custom_question,
                ground_truth=None,
                metadata={},
            )
        )
    elif run_all or limit:
        targets = questions_data["public"]
        if limit:
            targets = targets[:limit]
    else:
        # Default to first question
        if questions_data["public"]:
            targets.append(questions_data["public"][0])

    print(f"\n=======================================================")
    print(f"  GraphMind TigerGraph GraphRAG Runner ({len(targets)} question(s))")
    print(f"=======================================================\n")

    for i, q in enumerate(targets, start=1):
        print(f"[{i}/{len(targets)}] Processing Question ID: {q.question_id}")
        print(f"  Prompt: {q.question}")
        if q.ground_truth:
            print(f"  Ground Truth: {q.ground_truth}")

        result = tigergraph_rag.query(
            question=q.question,
            question_id=q.question_id,
            ground_truth=q.ground_truth,
        )

        print(f"  -> Answer: {result.answer}")
        print(f"  -> Entities Linked: {result.entities}")
        print(f"  -> Graph Paths ({len(result.graph_paths)}): {result.graph_paths[:2]}")
        print(f"  -> Evidence Count: {len(result.evidence)}")
        print(f"  -> Citations: {result.citations[:3]}")
        print(f"  -> Tokens: {result.total_tokens} (In: {result.input_tokens}, Out: {result.output_tokens})")
        print(f"  -> Latency: {result.latency_ms:.1f}ms (Graph: {result.graph_latency_ms:.1f}ms, LLM: {result.llm_latency_ms:.1f}ms)")
        if result.is_exact_match is not None:
            print(f"  -> Exact Match: {'YES [MATCH]' if result.is_exact_match else 'NO'}")
        print()

        # Persist trace
        out_path = os.path.join(results_dir, f"{q.question_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2)

    print(f"GraphRAG results successfully saved to {results_dir}/")


def main():
    parser = argparse.ArgumentParser(description="GraphMind TigerGraph GraphRAG CLI Runner")
    parser.add_argument("--question-id", help="Dataset question ID to evaluate (e.g. pub-001)")
    parser.add_argument("--question", help="Ad-hoc natural language question")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of evaluation questions")
    parser.add_argument("--all", action="store_true", help="Run against all public evaluation questions")
    parser.add_argument("--results-dir", default="evaluation/results/graphrag", help="Output directory")

    args = parser.parse_args()
    run_graphrag_cli(
        question_id=args.question_id,
        custom_question=args.question,
        limit=args.limit,
        run_all=args.all,
        results_dir=args.results_dir,
    )


if __name__ == "__main__":
    main()
