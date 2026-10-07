"""CLI runner for GraphMind ingestion pipeline."""

import argparse
import json
import os
import sys
import time
from datetime import datetime

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure project root and backend are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "../../.."))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app.core.logging import logger
from backend.app.ingestion.loader import load_documents_from_jsonl, load_questions_from_jsonl
from backend.app.ingestion.chunker import DocumentChunker
from backend.app.ingestion.vector_store import vector_store


def run_ingestion(
    process_documents: bool = False,
    process_questions: bool = False,
    corpus_path: str = "corpus/corpus.jsonl",
    public_q_path: str = "questions/eval_public.jsonl",
    hidden_q_path: str = "questions/eval_hidden.jsonl",
    output_report_path: str = "evaluation/results/ingestion_report.json",
    limit: int = None,
):
    """Executes the ingestion pipeline and writes a machine-readable statistics report."""
    start_time = time.time()
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "in_progress",
        "documents_processed": 0,
        "chunks_created": 0,
        "questions_loaded": 0,
        "embedding_count": 0,
        "public_questions": 0,
        "hidden_questions": 0,
        "errors": [],
        "duration_seconds": 0.0,
    }

    try:
        # 1. Ingest questions if requested
        if process_questions:
            logger.info("Starting evaluation questions ingestion...")
            questions = load_questions_from_jsonl(public_q_path, hidden_q_path)
            pub_count = len(questions["public"])
            hid_count = len(questions["hidden"])
            total_q = pub_count + hid_count
            report["public_questions"] = pub_count
            report["hidden_questions"] = hid_count
            report["questions_loaded"] = total_q
            logger.info(f"Questions loaded successfully: {pub_count} public, {hid_count} hidden.")

        # 2. Ingest documents and chunks if requested
        if process_documents:
            logger.info("Starting documents and chunks ingestion...")
            docs = load_documents_from_jsonl(corpus_path, limit=limit)
            report["documents_processed"] = len(docs)

            chunker = DocumentChunker(chunk_size=1000, chunk_overlap=150)
            chunks = chunker.chunk_documents(docs)
            report["chunks_created"] = len(chunks)

            # Index into ChromaDB
            indexed = vector_store.index_chunks(chunks)
            report["embedding_count"] = indexed

        report["status"] = "completed"

    except Exception as e:
        logger.error(f"Ingestion pipeline encountered an error: {e}")
        report["status"] = "failed"
        report["errors"].append(str(e))
        raise e

    finally:
        report["duration_seconds"] = round(time.time() - start_time, 2)
        os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
        with open(output_report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Ingestion report written to {output_report_path}: {report}")

    return report


def main():
    parser = argparse.ArgumentParser(description="GraphMind Ingestion Pipeline CLI")
    parser.add_argument("--documents", action="store_true", help="Process and index corpus documents")
    parser.add_argument("--questions", action="store_true", help="Process evaluation questions")
    parser.add_argument("--all", action="store_true", help="Process both documents and evaluation questions")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of documents for testing")
    parser.add_argument("--corpus-path", default="corpus/corpus.jsonl", help="Path to corpus JSONL")
    parser.add_argument("--public-questions", default="questions/eval_public.jsonl", help="Path to public questions JSONL")
    parser.add_argument("--hidden-questions", default="questions/eval_hidden.jsonl", help="Path to hidden questions JSONL")
    parser.add_argument("--report-path", default="evaluation/results/ingestion_report.json", help="Path to output report")

    args = parser.parse_args()

    # Default to --all if no specific flag passed
    if not (args.documents or args.questions or args.all):
        args.all = True

    process_docs = args.documents or args.all
    process_questions = args.questions or args.all

    run_ingestion(
        process_documents=process_docs,
        process_questions=process_questions,
        corpus_path=args.corpus_path,
        public_q_path=args.public_questions,
        hidden_q_path=args.hidden_questions,
        output_report_path=args.report_path,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
