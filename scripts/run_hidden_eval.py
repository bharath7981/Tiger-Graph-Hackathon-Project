"""Script to evaluate all 50 hidden test questions and generate competition submission artifacts.

Per the TigerGraph Hackathon Guidebook:
'50 hidden evaluation questions: you won't see the answers for these.
Run your system on all 50 and submit the raw outputs — tokens used, answers generated,
and agentic trace. We use these to score your system against our held-out ground truth.'
"""

import json
import os
import sys
import time
from pathlib import Path

# Ensure root directory is on python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.logging import logger
from backend.app.agents.graph import run_agentic_investigation


def run_hidden_evaluation(
    input_file: str = "questions/eval_hidden.jsonl",
    output_file: str = "evaluation/results/submission_hidden_predictions.jsonl",
    limit: int = None,
):
    """Executes Agentic GraphRAG on all hidden evaluation questions and writes submission JSONL."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    in_path = Path(input_file)
    if not in_path.exists():
        raise FileNotFoundError(f"Hidden evaluation file not found: {in_path}")

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    questions = []
    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))

    if limit:
        questions = questions[:limit]

    print(f"\n=======================================================")
    print(f"🐯 TigerGraph Hackathon: Hidden Evaluation Runner")
    print(f"Evaluating {len(questions)} hidden questions using LangGraph Agentic Swarm...")
    print(f"Output target: {out_path}")
    print(f"=======================================================\n")

    results = []
    start_total = time.time()

    with open(out_path, "w", encoding="utf-8") as out_f:
        for idx, q_item in enumerate(questions, 1):
            qid = q_item.get("qid")
            q_text = q_item.get("question")
            qtype = q_item.get("qtype", "unknown")

            print(f"[{idx}/{len(questions)}] Processing {qid} ({qtype}): {q_text[:60]}...")
            q_start = time.time()

            try:
                agent_res = run_agentic_investigation(
                    question=q_text,
                    question_id=qid,
                )
                
                submission_record = {
                    "qid": qid,
                    "question": q_text,
                    "qtype": qtype,
                    "answer": agent_res.get("answer", ""),
                    "citations": agent_res.get("citations", []),
                    "confidence": agent_res.get("confidence", 0.0),
                    "tokens": agent_res.get("tokens", 0),
                    "latency_ms": agent_res.get("latency_ms", round((time.time() - q_start) * 1000, 2)),
                    "steps": agent_res.get("steps", 0),
                    "tools_used": agent_res.get("tools_used", []),
                    "agents_used": agent_res.get("agents_used", []),
                    "agentic_trace": agent_res.get("trace", []),
                }

            except Exception as e:
                logger.error(f"Error on {qid}: {e}")
                submission_record = {
                    "qid": qid,
                    "question": q_text,
                    "qtype": qtype,
                    "answer": f"Investigation error: {str(e)}",
                    "citations": [],
                    "confidence": 0.0,
                    "tokens": 0,
                    "latency_ms": round((time.time() - q_start) * 1000, 2),
                    "steps": 0,
                    "tools_used": [],
                    "agents_used": [],
                    "agentic_trace": [],
                    "error": str(e),
                }

            out_f.write(json.dumps(submission_record, ensure_ascii=False) + "\n")
            out_f.flush()
            results.append(submission_record)

    total_time = round(time.time() - start_total, 2)
    avg_tokens = round(sum(r["tokens"] for r in results) / max(1, len(results)), 1)
    avg_latency = round(sum(r["latency_ms"] for r in results) / max(1, len(results)), 2)

    print(f"\n=======================================================")
    print(f"✅ Hidden Evaluation Complete!")
    print(f"Total Questions Evaluated: {len(results)}")
    print(f"Average Tokens: {avg_tokens}")
    print(f"Average Latency: {avg_latency} ms")
    print(f"Total Execution Time: {total_time} s")
    print(f"Submission File Ready: {out_path}")
    print(f"=======================================================\n")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run hidden evaluation for TigerGraph Hackathon")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions to process")
    parser.add_argument("--input", type=str, default="questions/eval_hidden.jsonl", help="Input JSONL path")
    parser.add_argument("--output", type=str, default="evaluation/results/submission_hidden_predictions.jsonl", help="Output JSONL path")
    args = parser.parse_args()

    run_hidden_evaluation(input_file=args.input, output_file=args.output, limit=args.limit)
