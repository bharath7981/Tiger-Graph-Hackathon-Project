"""CLI Runner for Agentic GraphRAG investigation pipeline."""

import argparse
import json
import os
import sys
from pathlib import Path

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.ingestion.loader import load_questions_from_jsonl
from backend.app.agents.graph import run_agentic_investigation


def main():
    parser = argparse.ArgumentParser(description="Run Agentic GraphRAG investigation runner")
    parser.add_argument("--question-id", type=str, help="Specific question ID to run (e.g. pub-001)")
    parser.add_argument("--limit", type=int, default=5, help="Number of questions to evaluate")
    parser.add_argument("--max-iterations", type=int, default=6, help="Max investigation loop iterations")
    parser.add_argument("--token-budget", type=int, default=8000, help="Token budget per question")
    parser.add_argument("--output-dir", type=str, default="evaluation/results/agentic", help="Output directory")

    args = parser.parse_args()

    # Load questions
    questions_file = Path("questions/eval_public.jsonl")
    if not questions_file.exists():
        logger.error(f"Questions file not found: {questions_file}")
        sys.exit(1)

    questions_dict = load_questions_from_jsonl(public_path=str(questions_file))
    questions = questions_dict.get("public", [])
    logger.info(f"Loaded {len(questions)} evaluation questions from {questions_file}")

    if args.question_id:
        selected_questions = [q for q in questions if q.question_id == args.question_id]
        if not selected_questions:
            logger.error(f"Question ID {args.question_id} not found in public questions.")
            sys.exit(1)
    else:
        selected_questions = questions[:args.limit]

    out_path = Path(args.output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print(f" AGENTIC GRAPHRAG INVESTIGATION HARNESS — Evaluating {len(selected_questions)} question(s)")
    print("=" * 80)

    results = []
    for idx, q in enumerate(selected_questions, 1):
        qtype = q.metadata.get("qtype", "unknown")
        gold_docs = q.metadata.get("gold_doc_ids", [])
        gold_ans = q.ground_truth

        print(f"\n[{idx}/{len(selected_questions)}] Investigating Question: {q.question_id}")
        print(f"Type: {qtype} | Gold Docs: {gold_docs}")
        print(f"Question: {q.question}")
        print("-" * 80)

        res = run_agentic_investigation(
            question=q.question,
            question_id=q.question_id,
            max_iterations=args.max_iterations,
            token_budget=args.token_budget,
        )

        res["question_type"] = qtype
        res["gold_document_ids"] = gold_docs
        res["gold_answer"] = gold_ans

        # Check gold doc hit
        citations = res.get("citations", [])
        gold_hit = any(g in citations for g in gold_docs)
        res["gold_hit"] = gold_hit

        print(f"Agents Used: {', '.join(res.get('agents_used', []))}")
        print(f"Tools Used : {', '.join(res.get('tools_used', []))}")
        print(f"Steps Taken: {res.get('steps')} | Total Tokens: {res.get('tokens')} | Latency: {res.get('latency_ms')}ms")
        print(f"Gold Hit   : {'YES (Matched ' + str([g for g in gold_docs if g in citations]) + ')' if gold_hit else 'NO'}")
        print(f"Answer     : {res.get('answer')[:250]}...")

        # Save individual trace
        file_name = out_path / f"{q.question_id}.json"
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)

        results.append(res)

    print("\n" + "=" * 80)
    print(" AGENTIC GRAPHRAG SUMMARY")
    print("=" * 80)
    hit_count = sum(1 for r in results if r.get("gold_hit"))
    avg_tokens = sum(r.get("tokens", 0) for r in results) / len(results)
    avg_latency = sum(r.get("latency_ms", 0.0) for r in results) / len(results)
    avg_steps = sum(r.get("steps", 0) for r in results) / len(results)

    print(f"Evaluated Questions: {len(results)}")
    print(f"Gold Document Hits : {hit_count}/{len(results)} ({hit_count/len(results)*100:.1f}%)")
    print(f"Average Steps      : {avg_steps:.1f}")
    print(f"Average Tokens     : {avg_tokens:.1f}")
    print(f"Average Latency    : {avg_latency:.2f}ms")
    print(f"Traces written to  : {out_path.resolve()}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
